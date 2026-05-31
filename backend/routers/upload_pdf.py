"""
upload_pdf.py  (FastAPI router)
-------------------------------
POST /api/upload
  Accepts a PDF or TXT file, runs the full ingestion pipeline synchronously,
  and returns success + stats. No manual steps. No restarts.

GET /api/upload/status
  Returns current FAISS index stats.
"""

import os
import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse

from ..services.chunk_text import create_chunks
from ..services.faiss_store import FAISSStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])

BOOKS_DIR = Path(os.getenv("BOOKS_DIR", "data/books"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_UPLOAD_MB", "100"))
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "application/octet-stream": None,   # allow generic binary, check extension
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_upload(upload: UploadFile) -> Path:
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    dest = BOOKS_DIR / upload.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return dest


def _extract_pages(file_path: Path) -> list[dict]:
    """Extract page dicts from PDF or TXT. Runs OCR if needed."""
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return [{"page_number": 1, "text": text}]

    if suffix != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}",
        )

    pages = []
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                pages.append({"page_number": i, "text": page.extract_text() or ""})
    except Exception as e:
        logger.warning("pdfplumber failed: %s. Trying PyPDF2.", e)
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(file_path))
            for i, page in enumerate(reader.pages, 1):
                pages.append({"page_number": i, "text": page.extract_text() or ""})
        except Exception as e2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"PDF extraction failed: {e2}",
            )

    # OCR fallback
    total_text = "".join(p["text"] for p in pages)
    if len(total_text.strip()) < 500:
        logger.info("Sparse PDF text (<500 chars), running OCR on %s", file_path.name)
        try:
            from pdf2image import convert_from_path
            import pytesseract
            images = convert_from_path(str(file_path), dpi=300)
            pages = [
                {"page_number": i + 1, "text": pytesseract.image_to_string(img, lang="eng")}
                for i, img in enumerate(images)
            ]
        except Exception as e:
            logger.error("OCR failed: %s. Returning sparse text extraction.", e)

    return pages


# ---------------------------------------------------------------------------
# POST /api/upload
# ---------------------------------------------------------------------------

@router.post("")
async def upload_file(file: UploadFile = File(...)):
    # --- Validation ---
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".pdf", ".txt"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only PDF and TXT are accepted.",
        )

    # Read entire file to check size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB.",
        )
    await file.seek(0)

    # --- Save ---
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    dest = BOOKS_DIR / file.filename
    with open(dest, "wb") as f:
        f.write(content)
    logger.info("Saved upload: %s (%.2f MB)", dest, size_mb)

    # --- Extract ---
    try:
        pages = _extract_pages(dest)
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Extraction error: {e}")

    pages_processed = len(pages)
    total_raw_chars = sum(len(p["text"]) for p in pages)
    logger.info("Extracted %d pages, %d chars from %s", pages_processed, total_raw_chars, file.filename)

    # --- Chunk ---
    book_name = dest.stem
    all_chunks = []
    for page in pages:
        if not page["text"].strip():
            continue
        chunks = create_chunks(
            text=page["text"],
            source=str(dest),
            book_name=book_name,
            page_number=page["page_number"],
            chunk_size=800,
            chunk_overlap=150,
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=(
                "No usable text could be extracted from this file. "
                "It may be a scanned image PDF without readable text, "
                "or the content is too sparse."
            ),
        )

    chunks_created = len(all_chunks)
    logger.info("Created %d chunks from %s", chunks_created, file.filename)

    # --- Embed + Index ---
    store = FAISSStore()
    added = store.add_documents(all_chunks)

    return JSONResponse(content={
        "success": True,
        "message": "Document indexed successfully",
        "filename": file.filename,
        "book_name": book_name,
        "pages_processed": pages_processed,
        "chunks_created": chunks_created,
        "chunks_added": added,
        "total_indexed": store.index.ntotal,
    })


# ---------------------------------------------------------------------------
# GET /api/upload/status
# ---------------------------------------------------------------------------

@router.get("/status")
async def index_status():
    store = FAISSStore()
    return store.stats()
