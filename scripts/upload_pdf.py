"""
upload_pdf.py
Carnatic GPT – Automatic PDF ingestion pipeline.
Called by the FastAPI /api/upload endpoint.
Pipeline: PDF → extract text → chunk → clean → embed → update FAISS
"""

import json
import hashlib
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Callable, Optional

import fitz  # PyMuPDF
class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size=800, chunk_overlap=150, separators=None, length_function=len, is_separator_regex=False):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
        self.length_function = length_function

    def split_text(self, text: str) -> list[str]:
        if not text:
            return []
            
        def _split(text_segment: str, separators: list[str]) -> list[str]:
            if self.length_function(text_segment) <= self.chunk_size:
                return [text_segment]
                
            if not separators:
                chunks = []
                for i in range(0, len(text_segment), self.chunk_size - self.chunk_overlap):
                    chunks.append(text_segment[i:i + self.chunk_size])
                return chunks
                
            sep = separators[0]
            remaining_seps = separators[1:]
            
            if sep == "":
                return _split(text_segment, remaining_seps)
                
            parts = text_segment.split(sep)
            chunks = []
            current_chunk = []
            current_len = 0
            
            for part in parts:
                part_len = self.length_function(part)
                if part_len > self.chunk_size:
                    if current_chunk:
                        chunks.append(sep.join(current_chunk))
                        current_chunk = []
                        current_len = 0
                    chunks.extend(_split(part, remaining_seps))
                elif current_len + part_len + (len(sep) if current_chunk else 0) <= self.chunk_size:
                    current_chunk.append(part)
                    current_len += part_len + (len(sep) if current_chunk else 0)
                else:
                    if current_chunk:
                        chunks.append(sep.join(current_chunk))
                    current_chunk = [part]
                    current_len = part_len
                    
            if current_chunk:
                chunks.append(sep.join(current_chunk))
                
            # Merge/post-process with overlap
            merged_chunks = []
            for chunk in chunks:
                if not merged_chunks:
                    merged_chunks.append(chunk)
                else:
                    last_chunk = merged_chunks[-1]
                    overlap_content = last_chunk[-self.chunk_overlap:] if len(last_chunk) > self.chunk_overlap else last_chunk
                    merged_chunks.append(overlap_content + sep + chunk)
            return merged_chunks

        return _split(text, self.separators)
from sentence_transformers import SentenceTransformer

from ingest import incremental_update

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
UPLOADS_DIR  = Path("data/uploads")
CHUNKS_PATH  = Path("data/chunks/cleaned_chunks.json")
MODEL_NAME   = "all-MiniLM-L6-v2"
CHUNK_SIZE   = 800
CHUNK_OVERLAP = 150
MIN_CHUNK_LEN = 100

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# OCR garbage patterns (same as chunk_text.py)
_OCR_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"^[^a-zA-Z]{10,}$",
        r"scanned\s+treatise\s+manuscript",
        r"page\s+\d+\s+of\s+\d+",
        r"\.{5,}",
        r"[^\x00-\x7F]{10,}",
        r"^\W+$",
        r"image\s+not\s+available",
        r"copyright\s+\d{4}",
        r"all\s+rights\s+reserved",
    ]
]


def _is_garbage(text: str) -> bool:
    text = text.strip()
    if len(text) < MIN_CHUNK_LEN:
        return True
    letter_count = sum(1 for c in text if c.isalpha())
    if letter_count < 40:
        return True
    for pat in _OCR_PATTERNS:
        if pat.search(text):
            return True
    non_print = sum(
        1 for c in text
        if unicodedata.category(c) in ("Cc", "Cf", "Cs")
    )
    if non_print / max(len(text), 1) > 0.05:
        return True
    return False


def _fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()


# ─────────────────────────────────────────────
# PIPELINE STEPS
# ─────────────────────────────────────────────
def extract_text_from_pdf(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    pages = []
    for page in doc:
        pages.append(page.get_text("text"))
    return "\n".join(pages)


def chunk_text(text: str, source: str) -> List[Dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
    )
    raw_chunks = splitter.split_text(text)
    chunks = []
    for raw in raw_chunks:
        raw = raw.strip()
        if _is_garbage(raw):
            continue
        chunks.append({
            "id": _fingerprint(raw),
            "content": raw,
            "source": source,
            "type": "theory",           # uploaded PDFs default to theory
        })
    return chunks


def _load_existing_chunks() -> List[Dict]:
    if CHUNKS_PATH.exists():
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_chunks(chunks: List[Dict]):
    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
def process_uploaded_pdf(
    pdf_path: Path,
    progress_cb: Optional[Callable[[str, int], None]] = None,
    model: Optional[SentenceTransformer] = None,
) -> Dict:
    """
    Full pipeline for an uploaded PDF.
    progress_cb(stage: str, pct: int) is called at each stage for SSE streaming.
    Returns a summary dict.
    """

    def notify(stage: str, pct: int):
        if progress_cb:
            progress_cb(stage, pct)
        else:
            print(f"  [{pct:3d}%] {stage}")

    notify("Extracting text from PDF …", 10)
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        return {"success": False, "error": "Could not extract text from PDF."}

    notify("Chunking text …", 30)
    source = f"uploads/{pdf_path.name}"
    new_chunks = chunk_text(raw_text, source)

    if not new_chunks:
        return {"success": False, "error": "No valid chunks after cleaning."}

    notify(f"Generated {len(new_chunks)} clean chunks. Deduplicating …", 50)
    existing = _load_existing_chunks()
    existing_ids = {c["id"] for c in existing}
    truly_new = [c for c in new_chunks if c["id"] not in existing_ids]

    if not truly_new:
        return {
            "success": True,
            "message": "All chunks already indexed.",
            "new_chunks": 0,
            "total_chunks": len(existing),
        }

    notify(f"Saving {len(truly_new)} new chunks …", 60)
    all_chunks = existing + truly_new
    _save_chunks(all_chunks)

    notify("Generating embeddings and updating FAISS …", 75)
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
    incremental_update(truly_new, model=model)

    notify("Done! Index updated.", 100)

    return {
        "success": True,
        "filename": pdf_path.name,
        "new_chunks": len(truly_new),
        "total_chunks": len(all_chunks),
        "message": f"Added {len(truly_new)} new chunks. Ready for questions.",
    }


# ─────────────────────────────────────────────
# CLI TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scripts/upload_pdf.py path/to/file.pdf")
        sys.exit(1)
    result = process_uploaded_pdf(Path(sys.argv[1]))
    print("\nResult:", json.dumps(result, indent=2))
