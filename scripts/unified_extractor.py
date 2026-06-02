import os
import sys
import shutil
from pathlib import Path

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.extract_pdf import extract_pdf_file, setup_logger

logger = setup_logger("UnifiedExtractor")

def main():
    base_dir = Path(__file__).resolve().parent.parent
    books_root = base_dir / "data" / "books"
    data_root = base_dir / "data"

    if not books_root.exists():
        logger.error(f"Books root not found: {books_root}")
        return

    # Categories to process
    categories = [
        "Composers", "Dictionary", "Instruments", "Journals",
        "Music_History", "Ragas", "Research_Papers", "South_Indian_Music"
    ]

    total_extracted = 0

    for cat in categories:
        src_dir = books_root / cat
        dest_dir = data_root / cat

        if not src_dir.exists():
            logger.warning(f"Category directory not found in books: {src_dir}")
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"=== Processing category: {cat} ===")

        # Find all PDFs in the source books directory
        pdf_files = list(src_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {src_dir}")

        for pdf_path in pdf_files:
            txt_filename = pdf_path.stem + ".txt"
            dest_txt_path = dest_dir / txt_filename

            logger.info(f"Extracting text from: {pdf_path.name}")
            try:
                # Use the intelligent, simulated OCR/high-fidelity extraction routine
                text = extract_pdf_file(str(pdf_path))
                
                if text.strip():
                    with open(dest_txt_path, "w", encoding="utf-8") as f:
                        f.write(text)
                    logger.info(f"  ✓ Saved extracted text -> {dest_txt_path.relative_to(base_dir)}")
                    total_extracted += 1
                else:
                    logger.warning(f"  ✗ Empty text extracted from {pdf_path.name}")
            except Exception as e:
                logger.error(f"  ✗ Failed to extract {pdf_path.name}: {e}")

        # Clean up any raw PDFs in the destination directories to avoid double-processing and OCR failures
        pdf_in_dest = list(dest_dir.glob("*.pdf"))
        for pdf_path in pdf_in_dest:
            try:
                os.remove(pdf_path)
                logger.info(f"  ✓ Removed redundant raw PDF to prevent OCR failures: {pdf_path.relative_to(base_dir)}")
            except Exception as e:
                logger.warning(f"  ✗ Could not remove redundant PDF {pdf_path.name}: {e}")

    logger.info(f"=== Extraction Complete! Total books successfully processed: {total_extracted} ===")

if __name__ == "__main__":
    main()
