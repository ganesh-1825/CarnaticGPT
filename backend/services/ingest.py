"""
ingest.py
---------
Bulk ingestion pipeline. Reads all source data from:
  - PDF/TXT files in data/ subfolders
  - CarnaticSongsDatabase.csv
  - Audio folder metadata

Cleans, chunks, embeds, and stores everything in FAISS.
Safe to re-run: duplicate detection prevents double-indexing.

Usage:
  python -m backend.services.ingest
  python -m backend.services.ingest --clean   # wipe index and re-index
"""

import os
import sys
import csv
import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

THEORY_FOLDERS = [
    "Composers", "Dictionary", "Instruments", "Journals",
    "Music_History", "Ragas", "South_Indian_Music",
]
RESEARCH_FOLDERS = ["Research_Papers"]
MUSIC_CSV_GLOB = ["music_dataset/*.csv", "music_dataset/**/*.csv"]
AUDIO_DIR = DATA_DIR / "audio"


# ---------------------------------------------------------------------------
# PDF / TXT text extraction
# ---------------------------------------------------------------------------

def _extract_pdf_pages(file_path: Path) -> list[dict]:
    """Extract text page-by-page from a PDF. Falls back to PyMuPDF, then PyPDF2, then OCR if needed."""
    pages = []
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                pages.append({"page_number": i, "text": text})
    except Exception as e:
        logger.warning("pdfplumber failed for %s: %s. Trying PyMuPDF (fitz).", file_path, e)
        try:
            import fitz
            doc = fitz.open(str(file_path))
            for i, page in enumerate(doc, 1):
                text = page.get_text("text") or ""
                pages.append({"page_number": i, "text": text})
        except Exception as e2:
            logger.warning("PyMuPDF failed for %s: %s. Trying PyPDF2.", file_path, e2)
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(str(file_path))
                for i, page in enumerate(reader.pages, 1):
                    text = page.extract_text() or ""
                    pages.append({"page_number": i, "text": text})
            except Exception as e3:
                logger.error("PyPDF2 also failed for %s: %s", file_path, e3)
                return []

    # OCR fallback: if total text is very short
    total_text = "".join(p["text"] for p in pages)
    if len(total_text.strip()) < 500:
        logger.info("Sparse text detected in %s, running OCR...", file_path.name)
        try:
            pages = _ocr_pdf(file_path)
        except Exception as e:
            logger.warning("OCR failed for %s: %s — skipping", file_path.name, e)
            pages = []

    return pages


def _ocr_pdf(file_path: Path) -> list[dict]:
    try:
        from pdf2image import convert_from_path
        import pytesseract
        images = convert_from_path(str(file_path), dpi=300)
        pages = []
        for i, img in enumerate(images, 1):
            text = pytesseract.image_to_string(img, lang="eng")
            pages.append({"page_number": i, "text": text})
        return pages
    except Exception as e:
        logger.error("OCR failed for %s: %s", file_path, e)
        return []


def _extract_txt(file_path: Path) -> list[dict]:
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        # Treat entire file as page 1
        return [{"page_number": 1, "text": text}]
    except Exception as e:
        logger.error("Failed to read TXT %s: %s", file_path, e)
        return []


def _extract_file(file_path: Path) -> list[dict]:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_pages(file_path)
    if suffix == ".txt":
        return _extract_txt(file_path)
    logger.debug("Skipping unsupported file type: %s", file_path)
    return []


# ---------------------------------------------------------------------------
# Ingest a single document file
# ---------------------------------------------------------------------------

def ingest_document(file_path: Path, force_category: str | None = None) -> int:
    """Extract, chunk and index a single PDF/TXT file. Returns chunks added."""
    from .chunk_text import create_chunks
    from .faiss_store import FAISSStore

    store = FAISSStore()
    book_name = file_path.stem
    source = str(file_path)

    if store.is_book_indexed(book_name):
        logger.info("Already indexed: %s -- skipping.", book_name)
        return 0

    pages = _extract_file(file_path)
    if not pages:
        logger.warning("No text extracted from %s", file_path)
        return 0

    all_chunks = []
    for page in pages:
        if not page["text"].strip():
            continue
        chunks = create_chunks(
            text=page["text"],
            source=source,
            book_name=book_name,
            page_number=page["page_number"],
            chunk_size=330,
            chunk_overlap=65,
            force_category=force_category,
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        logger.warning("No quality chunks from %s", file_path)
        return 0

    added = store.add_documents(all_chunks)
    logger.info("[%s] %d chunks indexed.", book_name, added)
    return added


# ---------------------------------------------------------------------------
# Ingest CSV music dataset
# ---------------------------------------------------------------------------

def ingest_csv(csv_path: Path) -> int:
    from .chunk_text import csv_row_to_text, create_chunks, deduplicate_chunks
    from .faiss_store import FAISSStore

    store = FAISSStore()
    book_name = csv_path.stem
    source = str(csv_path)

    if store.is_book_indexed(book_name):
        logger.info("Already indexed: %s -- skipping.", book_name)
        return 0

    all_chunks = []
    try:
        with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                text = csv_row_to_text(row)
                if len(text.strip()) < 30:
                    continue
                chunks = create_chunks(
                    text=text,
                    source=source,
                    book_name=book_name,
                    page_number=row_num,
                    chunk_size=330,
                    chunk_overlap=0,   # CSV rows: no overlap needed
                    force_category="music",
                )
                for chunk in chunks:
                    chunk["song"] = row.get("Song Name") or row.get("Song")
                    chunk["raga"] = row.get("Ragam") or row.get("Raga")
                    chunk["composer"] = row.get("Composer")
                    chunk["melakarta"] = row.get("Janya Number") or row.get("Melakarta")
                    chunk["shruti"] = row.get("Shruti")
                    chunk["youtube"] = row.get("Youtube Link") or row.get("Youtube")
                all_chunks.extend(chunks)
    except Exception as e:
        logger.error("Failed to read CSV %s: %s", csv_path, e)
        return 0

    all_chunks = deduplicate_chunks(all_chunks)
    if not all_chunks:
        logger.warning("No quality chunks from CSV %s", csv_path)
        return 0

    added = store.add_documents(all_chunks)
    logger.info("[%s CSV] %d chunks indexed.", book_name, added)
    return added


# ---------------------------------------------------------------------------
# Ingest audio metadata
# ---------------------------------------------------------------------------

def ingest_audio_metadata() -> int:
    """Index audio folder structure as searchable metadata chunks."""
    from .chunk_text import create_chunks
    from .faiss_store import FAISSStore

    if not AUDIO_DIR.exists():
        logger.info("No audio directory found, skipping audio metadata ingestion.")
        return 0

    store = FAISSStore()

    # Scan audio directory for raga folders
    audio_index = {}
    for raga_dir in sorted(AUDIO_DIR.iterdir()):
        if raga_dir.is_dir():
            audio_files = {}
            for audio_file in raga_dir.iterdir():
                if audio_file.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac"):
                    audio_files[audio_file.stem] = str(audio_file)
            if audio_files:
                audio_index[raga_dir.name] = audio_files

    if not audio_index:
        return 0

    chunks = []
    for raga_name, audio_files in audio_index.items():
        text_lines = [
            f"Raga: {raga_name}",
            f"Available audio recordings: {', '.join(audio_files.keys())}",
            f"Audio files: {'; '.join(f'{k}: {v}' for k, v in audio_files.items())}",
            f"This audio collection contains {len(audio_files)} recordings for raga {raga_name}.",
        ]
        text = "\n".join(text_lines)
        raga_chunks = create_chunks(
            text=text,
            source=str(AUDIO_DIR / raga_name),
            book_name=f"audio_{raga_name}",
            page_number=1,
            chunk_size=330,
            chunk_overlap=0,
            force_category="audio",
        )
        chunks.extend(raga_chunks)

    if not chunks:
        return 0

    added = store.add_documents(chunks)
    logger.info("[Audio Metadata] %d chunks indexed.", added)
    return added


# ---------------------------------------------------------------------------
# Full bulk ingestion
# ---------------------------------------------------------------------------

def run_full_ingestion(clean: bool = False) -> dict:
    """
    Run complete ingestion across all data sources.
    If clean=True, wipes FAISS index first.
    """
    from .faiss_store import FAISSStore

    if clean:
        logger.warning("Clean mode: wiping existing FAISS index.")
        store = FAISSStore()
        store._create_new_index()
        store.save()

    totals = {"theory": 0, "research": 0, "music": 0, "audio": 0}

    # --- Theory books ---
    for folder_name in THEORY_FOLDERS:
        folder = DATA_DIR / folder_name
        if not folder.exists():
            logger.debug("Theory folder not found: %s", folder)
            continue
        for file_path in sorted(folder.rglob("*")):
            if file_path.suffix.lower() in (".pdf", ".txt") and file_path.is_file():
                added = ingest_document(file_path, force_category="theory")
                totals["theory"] += added

    # --- Research papers ---
    for folder_name in RESEARCH_FOLDERS:
        folder = DATA_DIR / folder_name
        if not folder.exists():
            continue
        for file_path in sorted(folder.rglob("*")):
            if file_path.suffix.lower() in (".pdf", ".txt") and file_path.is_file():
                added = ingest_document(file_path, force_category="research")
                totals["research"] += added

    # --- Music CSV(s) ---
    for pattern in MUSIC_CSV_GLOB:
        for csv_path in sorted(DATA_DIR.glob(pattern)):
            if csv_path.is_file():
                added = ingest_csv(csv_path)
                totals["music"] += added

    # --- Audio metadata ---
    totals["audio"] = ingest_audio_metadata()

    total_added = sum(totals.values())
    logger.info(
        "Ingestion complete. Total chunks added: %d | theory=%d research=%d music=%d audio=%d",
        total_added, totals["theory"], totals["research"], totals["music"], totals["audio"],
    )
    return {"total_added": total_added, "by_type": totals}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CarnaticGPT bulk ingestion")
    parser.add_argument("--clean", action="store_true", help="Wipe index before ingesting")
    args = parser.parse_args()

    result = run_full_ingestion(clean=args.clean)
    print(f"\nDone. {result['total_added']} total chunks indexed.")
    print(f"  Theory:   {result['by_type']['theory']}")
    print(f"  Research: {result['by_type']['research']}")
    print(f"  Music:    {result['by_type']['music']}")
    print(f"  Audio:    {result['by_type']['audio']}")
