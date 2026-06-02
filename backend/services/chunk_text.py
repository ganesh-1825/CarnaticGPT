"""
chunk_text.py
-------------
Cleans raw extracted text, filters low-quality content, removes duplicates,
creates semantic chunks with rich metadata, and categorises every chunk.

Chunk targets (after cleaning):
  Theory books      → 10,000-15,000
  Research papers   →  3,000-6,000
  Music dataset     →  5,000-10,000
  Audio metadata    →    500-1,000
"""

import re
import hashlib
import unicodedata
from typing import Optional

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

# ---------------------------------------------------------------------------
# Category keyword maps
# ---------------------------------------------------------------------------

THEORY_KEYWORDS = [
    "shruti", "swara", "saptha swara", "shadja", "rishabha", "gandhara",
    "madhyama", "panchama", "dhaivata", "nishada", "melakarta", "janya raga",
    "arohana", "avarohana", "gamaka", "melapakarta", "vadi", "samvadi",
    "anuvadi", "vivadi", "graha", "nyasa", "amsa", "lakshana", "raga lakshana",
    "tala", "adi tala", "rupaka", "misra chapu", "khanda chapu", "tisra",
    "chatusra", "sankirna", "laghu", "drutam", "anudrutam", "kriti", "varnam",
    "geetam", "alapana", "niraval", "kalpana swaras", "tani avartanam",
    "manodharma", "ragam tanam pallavi", "pallavi", "anupallavi", "charanam",
    "sangati", "nadai", "carnatic", "karnatik", "hindustani", "shruthi",
    "ragamalika", "tanavarnam", "pada varnam", "swarajati", "javali",
    "thillana", "padam", "keerthanam", "devaranama", "ugabhoga",
]

MUSIC_DATASET_KEYWORDS = [
    "composer:", "raga:", "tala:", "song:", "ragam:", "vocalist",
    "carnatic song", "composition", "krithi", "concert", "album",
    "recording", "performer", "discography",
]

RESEARCH_KEYWORDS = [
    "abstract", "introduction", "conclusion", "methodology", "literature review",
    "references", "doi:", "issn", "journal of", "proceedings", "conference",
    "hypothesis", "experiment", "results", "discussion", "figure", "table",
    "citation", "bibliography", "et al.", "ibid",
]

OCR_GARBAGE_PATTERNS = [
    r"^[^\w\s]{3,}$",
    r"(?:[^\x00-\x7F]){5,}",
    r"(\b\w\b[\s]{0,2}){5,}",
    r"[|]{2,}",
    r"[_]{4,}",
    r"[.]{4,}",
    r"^\s*\d+\s*$",
    r"^[ivxlcdm]+\.?\s*$",
    r"scanned\s+(?:page|image|document)",
    r"(?:digitized|digitised)\s+by",
    r"www\.[^\s]{3,}\.[a-z]{2,}",
]

MANUSCRIPT_JUNK_PATTERNS = [
    r"manuscript\s+(?:page|folio)",
    r"palm\s*leaf",
    r"(?:telugu|tamil|kannada|devanagari)\s+script\s+(?:text|characters)",
    r"(?:indecipherable|illegible|unclear)\s+(?:text|portion|section)",
    r"^\s*(?:fig(?:ure)?\.?\s*\d+|plate\s*\d+|image\s*\d+)\s*$",
]

# ---------------------------------------------------------------------------
# Core cleaning
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", "").replace("\ufeff", "")
    text = re.sub(r"[''`]", "'", text)
    text = re.sub(r"[\u201c\u201d]", '"', text)
    text = re.sub(r"\u2014|\u2013", "-", text)
    text = re.sub(r"\r\n|\r", "\n", text)
    return text


def _remove_page_artifacts(text: str) -> str:
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^\s*-?\s*\d{1,4}\s*-?\s*$", stripped):
            continue
        if len(stripped) < 15 and not re.search(r"[a-z]{3,}", stripped, re.I):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _collapse_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _remove_ocr_garbage_lines(text: str) -> str:
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append(line)
            continue
        is_garbage = False
        for pat in OCR_GARBAGE_PATTERNS + MANUSCRIPT_JUNK_PATTERNS:
            if re.search(pat, stripped, re.I):
                is_garbage = True
                break
        non_ascii = sum(1 for c in stripped if ord(c) > 127)
        if len(stripped) > 0 and (non_ascii / len(stripped)) > 0.40:
            is_garbage = True
        if not is_garbage:
            cleaned.append(line)
    return "\n".join(cleaned)


def _remove_duplicate_sentences(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    seen: set = set()
    result = []
    for sent in sentences:
        key = re.sub(r"\s+", " ", sent.strip().lower())
        if key and key not in seen:
            seen.add(key)
            result.append(sent)
    return " ".join(result)


def clean_text(text: str) -> str:
    text = _normalize(text)
    text = _remove_page_artifacts(text)
    text = _remove_ocr_garbage_lines(text)
    text = _collapse_whitespace(text)
    text = _remove_duplicate_sentences(text)
    return text.strip()


# ---------------------------------------------------------------------------
# Quality gate
# ---------------------------------------------------------------------------

def _is_quality_chunk(text: str) -> bool:
    stripped = text.strip()
    # Structured key-value metadata (e.g. Song:, Raga:, Audio:) bypasses sentence-ending checks
    if re.search(r"^(?:Song|Raga|Composer|Youtube|Available audio|Audio files):", stripped, re.I):
        return len(stripped) >= 30
    if len(stripped) < 100:
        return False
    if not re.search(r"[a-zA-Z]{3,}.*[.!?]", stripped):
        return False
    non_ascii = sum(1 for c in stripped if ord(c) > 127)
    if len(stripped) > 0 and (non_ascii / len(stripped)) > 0.30:
        return False
    alpha = sum(1 for c in stripped if c.isalpha())
    if len(stripped) > 0 and (alpha / len(stripped)) < 0.40:
        return False
    for pat in MANUSCRIPT_JUNK_PATTERNS:
        if re.search(pat, stripped, re.I):
            return False
    return True


# ---------------------------------------------------------------------------
# Category detection
# ---------------------------------------------------------------------------

def _detect_category(text: str, source_path: str = "") -> str:
    lower = text.lower() + " " + source_path.lower()
    path_lower = source_path.lower()
    if any(p in path_lower for p in ["research_paper", "journal", "research"]):
        return "research"
    if any(p in path_lower for p in ["music_dataset", "carnaticsongsdatabase", ".csv"]):
        return "music"
    if any(p in path_lower for p in ["audio", ".mp3", ".wav"]):
        return "audio"
    theory_score = sum(1 for kw in THEORY_KEYWORDS if kw in lower)
    music_score = sum(1 for kw in MUSIC_DATASET_KEYWORDS if kw in lower)
    research_score = sum(1 for kw in RESEARCH_KEYWORDS if kw in lower)
    scores = {"theory": theory_score, "music": music_score, "research": research_score}
    best = max(scores, key=scores.get)
    if scores[best] >= 2:
        return best
    return "theory"


# ---------------------------------------------------------------------------
# Content hash for deduplication
# ---------------------------------------------------------------------------

def _content_hash(text: str) -> str:
    normalised = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalised.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# CSV row -> text block
# ---------------------------------------------------------------------------

def csv_row_to_text(row: dict) -> str:
    parts = []
    field_map = {
        "song": "Song", "title": "Song",
        "raga": "Raga", "ragam": "Raga",
        "tala": "Tala", "thala": "Tala",
        "composer": "Composer", "artist": "Composer",
        "lyricist": "Lyricist",
        "language": "Language",
        "description": "Description",
        "notes": "Notes",
        "meaning": "Meaning",
        "type": "Type",
    }
    used = set()
    for raw_key, label in field_map.items():
        for actual_key in row:
            if actual_key.strip().lower() == raw_key and label not in used:
                val = str(row[actual_key]).strip()
                if val and val.lower() not in ("nan", "none", "", "unknown"):
                    parts.append(f"{label}: {val}")
                    used.add(label)
    for k, v in row.items():
        label = k.strip().title()
        if label not in used:
            val = str(v).strip()
            if val and val.lower() not in ("nan", "none", "", "unknown"):
                parts.append(f"{label}: {val}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main chunking function
# ---------------------------------------------------------------------------

def create_chunks(
    text: str,
    source: str,
    book_name: str,
    page_number: int = 0,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    force_category: Optional[str] = None,
) -> list:
    """
    Cleans text, splits into semantic chunks, filters low-quality chunks,
    deduplicates, and returns list of chunk dicts ready for embedding.

    Each chunk dict:
    {
        "id":          str,   # sha256 content hash (first 16 hex chars)
        "content":     str,
        "source":      str,
        "book_name":   str,
        "page_number": int,
        "type":        str,   # theory | music | research | audio
        "category":    str,   # alias for type
        "chunk_index": int,
        "char_count":  int,
    }
    """
    text = clean_text(text)
    if not text:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )

    raw_chunks = splitter.split_text(text)
    seen_hashes: set = set()
    result: list = []
    category = force_category or _detect_category(text, source)

    for idx, chunk in enumerate(raw_chunks):
        chunk = chunk.strip()
        if not _is_quality_chunk(chunk):
            continue
        h = _content_hash(chunk)
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        result.append({
            "id": h,
            "content": chunk,
            "source": source,
            "book_name": book_name,
            "page_number": page_number,
            "type": category,
            "category": category,
            "chunk_index": idx,
            "char_count": len(chunk),
        })

    return result


def deduplicate_chunks(chunks: list) -> list:
    seen: set = set()
    result: list = []
    for chunk in chunks:
        h = chunk.get("id") or _content_hash(chunk["content"])
        if h not in seen:
            seen.add(h)
            result.append(chunk)
    return result