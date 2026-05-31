"""
chunk_text.py
Carnatic GPT – Production chunking & cleaning pipeline.
Reads all source folders, cleans OCR garbage, deduplicates,
and writes cleaned chunks to data/chunks/cleaned_chunks.json
"""

import os
import sys
import re
import json
import hashlib
import unicodedata
from pathlib import Path
from typing import List, Dict

# Reconfigure stdout to use UTF-8 on Windows console to avoid encoding crashes
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


import fitz  # PyMuPDF
import pandas as pd
class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size=800, chunk_overlap=150, separators=None, length_function=len):
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



# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DATA_ROOT = Path("data")
CHUNKS_OUT = DATA_ROOT / "chunks" / "cleaned_chunks.json"

THEORY_FOLDERS = [
    "Composers", "Dictionary", "Instruments",
    "Music_History", "Ragas", "South_Indian_Music"
]
RESEARCH_FOLDERS = ["Research_Papers", "Journals"]
MUSIC_CSV = DATA_ROOT / "music_dataset" / "CarnaticSongsDatabase.csv"
AUDIO_ROOT = DATA_ROOT / "audio"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
MIN_CHUNK_LEN = 100

# ─────────────────────────────────────────────
# OCR GARBAGE DETECTION
# ─────────────────────────────────────────────
OCR_GARBAGE_PATTERNS = [
    r"^[^a-zA-Z]{10,}$",                        # lines with no letters
    r"scanned\s+treatise\s+manuscript",          # explicit scan markers
    r"page\s+\d+\s+of\s+\d+",                   # page markers only
    r"\.{5,}",                                   # long dot sequences
    r"[^\x00-\x7F]{10,}",                        # long non-ASCII runs
    r"^\W+$",                                    # only punctuation/symbols
    r"image\s+not\s+available",
    r"copyright\s+\d{4}",
    r"all\s+rights\s+reserved",
]
OCR_COMPILED = [re.compile(p, re.IGNORECASE) for p in OCR_GARBAGE_PATTERNS]


def is_garbage(text: str) -> bool:
    text = text.strip()
    if len(text) < MIN_CHUNK_LEN:
        return True
    # Must have at least one sentence-ending punctuation or be a proper definition
    letter_count = sum(1 for c in text if c.isalpha())
    if letter_count < 40:
        return True
    for pat in OCR_COMPILED:
        if pat.search(text):
            return True
    # High ratio of non-printable / control chars → garbage
    non_print = sum(
        1 for c in text
        if unicodedata.category(c) in ("Cc", "Cf", "Cs")
    )
    if non_print / max(len(text), 1) > 0.05:
        return True
    return False


# ─────────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────────
def fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()


# ─────────────────────────────────────────────
# PDF EXTRACTION
# ─────────────────────────────────────────────
def extract_pdf_text(pdf_path: Path) -> str:
    try:
        doc = fitz.open(str(pdf_path))
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        return "\n".join(pages)
    except Exception as e:
        print(f"  [WARN] Could not extract {pdf_path}: {e}")
        return ""


# ─────────────────────────────────────────────
# CHUNKER
# ─────────────────────────────────────────────
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
)


def make_chunks(
    text: str,
    source: str,
    chunk_type: str,
    extra_meta: dict = None,
) -> List[Dict]:
    raw_chunks = splitter.split_text(text)
    chunks = []
    for raw in raw_chunks:
        raw = raw.strip()
        if is_garbage(raw):
            continue
        meta = {
            "id": fingerprint(raw),
            "content": raw,
            "source": source,
            "type": chunk_type,
        }
        if extra_meta:
            meta.update(extra_meta)
        chunks.append(meta)
    return chunks


# ─────────────────────────────────────────────
# FOLDER PROCESSORS
# ─────────────────────────────────────────────
def process_folder(folder_name: str, chunk_type: str) -> List[Dict]:
    folder = DATA_ROOT / folder_name
    all_chunks: List[Dict] = []
    if not folder.exists():
        print(f"  [SKIP] Folder not found: {folder}")
        return all_chunks
    for pdf_path in folder.rglob("*.pdf"):
        print(f"  Extracting: {pdf_path.name}")
        text = extract_pdf_text(pdf_path)
        if not text.strip():
            continue
        chunks = make_chunks(
            text,
            source=str(pdf_path.relative_to(DATA_ROOT)),
            chunk_type=chunk_type,
        )
        all_chunks.extend(chunks)
        print(f"    -> {len(chunks)} clean chunks")
    return all_chunks



def process_music_csv() -> List[Dict]:
    if not MUSIC_CSV.exists():
        print(f"  [SKIP] CSV not found: {MUSIC_CSV}")
        return []
    df = pd.read_csv(MUSIC_CSV, encoding="utf-8", on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]
    # Normalise column names to lowercase for safety
    col_map = {c: c.lower().replace(" ", "_") for c in df.columns}
    df.rename(columns=col_map, inplace=True)

    def get_col(row, *candidates):
        for c in candidates:
            if c in row.index and pd.notna(row[c]):
                return str(row[c]).strip()
        return ""

    chunks = []
    seen = set()
    for _, row in df.iterrows():
        song = get_col(row, "song_name", "song", "title")
        raga = get_col(row, "ragam", "raga", "raagam")
        composer = get_col(row, "composer", "vaggeyakara")
        youtube = get_col(row, "youtube_link", "youtube", "link", "url")
        tala = get_col(row, "tala", "talam")
        aroha = get_col(row, "arohana", "arohanam")
        avaroha = get_col(row, "avarohana", "avarohanam")

        if not song and not raga:
            continue

        content = f"Song: {song}\nRagam: {raga}\nComposer: {composer}"
        if tala:
            content += f"\nTala: {tala}"
        if aroha:
            content += f"\nArohana: {aroha}"
        if avaroha:
            content += f"\nAvarohana: {avaroha}"

        fp = fingerprint(content)
        if fp in seen:
            continue
        seen.add(fp)

        if len(content) < 20:
            continue

        chunks.append({
            "id": fp,
            "content": content,
            "source": "music_dataset/CarnaticSongsDatabase.csv",
            "type": "music",
            "song": song,
            "raga": raga,
            "composer": composer,
            "youtube": youtube,
            "tala": tala,
            "arohana": aroha,
            "avarohana": avaroha,
        })
    return chunks


def process_audio_metadata() -> List[Dict]:
    chunks = []
    if not AUDIO_ROOT.exists():
        print(f"  [SKIP] Audio root not found: {AUDIO_ROOT}")
        return chunks
    seen = set()
    for raga_dir in sorted(AUDIO_ROOT.iterdir()):
        if not raga_dir.is_dir():
            continue
        raga_name = raga_dir.name
        audio_files = list(raga_dir.glob("*.mp3")) + list(raga_dir.glob("*.wav"))
        if not audio_files:
            continue
        file_names = ", ".join(f.name for f in audio_files)
        content = (
            f"Raga: {raga_name}\n"
            f"Audio files available: {file_names}\n"
            f"Path: audio/{raga_name}/"
        )
        fp = fingerprint(content)
        if fp in seen:
            continue
        seen.add(fp)
        chunks.append({
            "id": fp,
            "content": content,
            "source": f"audio/{raga_name}",
            "type": "audio_metadata",
            "raga": raga_name,
            "audio_path": f"audio/{raga_name}",
            "files": [f.name for f in audio_files],
        })
    return chunks


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    CHUNKS_OUT.parent.mkdir(parents=True, exist_ok=True)
    all_chunks: List[Dict] = []
    seen_ids: set = set()

    print("\n=== Processing Theory Books ===")
    for folder in THEORY_FOLDERS:
        chunks = process_folder(folder, "theory")
        all_chunks.extend(chunks)
    print(f"  Theory total (before dedup): {sum(1 for c in all_chunks if c['type']=='theory')}")

    print("\n=== Processing Research Papers ===")
    for folder in RESEARCH_FOLDERS:
        chunks = process_folder(folder, "research")
        all_chunks.extend(chunks)

    print("\n=== Processing Music CSV ===")
    music_chunks = process_music_csv()
    all_chunks.extend(music_chunks)
    print(f"  Music rows: {len(music_chunks)}")

    print("\n=== Processing Audio Metadata ===")
    audio_chunks = process_audio_metadata()
    all_chunks.extend(audio_chunks)
    print(f"  Audio raga entries: {len(audio_chunks)}")

    # Global deduplication
    print("\n=== Deduplicating ===")
    unique_chunks = []
    for chunk in all_chunks:
        cid = chunk["id"]
        if cid not in seen_ids:
            seen_ids.add(cid)
            unique_chunks.append(chunk)

    # Stats
    by_type: Dict[str, int] = {}
    for c in unique_chunks:
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1

    print(f"\n=== Final Chunk Counts ===")
    for t, count in sorted(by_type.items()):
        print(f"  {t:<20}: {count:,}")
    print(f"  {'TOTAL':<20}: {len(unique_chunks):,}")

    with open(CHUNKS_OUT, "w", encoding="utf-8") as f:
        json.dump(unique_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Saved to {CHUNKS_OUT}")


def chunk_document(text: str, metadata: dict, chunk_size: int = 800, chunk_overlap: int = 150) -> list[dict]:
    """Helper chunking function called by the active backend document ingestion pipeline."""
    local_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
    )
    raw_chunks = local_splitter.split_text(text)

    chunks = []
    
    current_page = 1
    for idx, raw in enumerate(raw_chunks):
        raw = raw.strip()
        if not raw:
            continue
            
        # Detect page number if embedded in text (e.g. from pypdf extraction format "--- PAGE X ---")
        page_matches = re.findall(r"--- PAGE (\d+) ---", raw)
        if page_matches:
            current_page = int(page_matches[-1])
            
        chunk_meta = metadata.copy()
        chunk_meta["page"] = current_page
        
        chunks.append({
            "chunk_id": f"{metadata.get('book_id', 'doc')}_p{current_page}_c{idx+1}",
            "text": raw,
            "metadata": chunk_meta
        })
    return chunks


if __name__ == "__main__":
    main()