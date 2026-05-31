"""
query_router.py
---------------
Classifies every incoming query into one of three routing modes:
  - "theory"  → search theory books, dictionaries, ragas, instruments folders only
  - "music"   → search CSV music dataset only
  - "hybrid"  → search both (theory + music)

The router also extracts the raga name from the query (if present)
so the audio mapping layer can pick the correct audio files.
"""

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Keyword tables
# ---------------------------------------------------------------------------

THEORY_TRIGGER_PHRASES = [
    "what is", "what are", "define", "definition of", "meaning of",
    "explain", "describe", "how does", "how do", "difference between",
    "compare", "contrast", "types of", "kinds of", "classification",
    "structure of", "characteristics of", "features of", "concept of",
    "theory of", "origin of", "history of", "significance of",
    "importance of", "role of", "purpose of", "examples of",
    "tell me about", "give me information", "elaborate on",
]

MUSIC_TRIGGER_PHRASES = [
    "song", "songs", "list of songs", "compositions by", "composed by",
    "composer", "vocalist", "performer", "singer", "concert", "album",
    "discography", "recording", "play audio", "play the", "listen to",
    "who composed", "who sang", "who sings", "krithi", "kriti",
    "keerthana", "keerthanam", "popular compositions", "famous songs",
    "show me songs", "find songs", "search songs",
]

AUDIO_TRIGGER_PHRASES = [
    "play", "listen", "audio", "sound", "hear", "alapana", "arohana",
    "avarohana", "sample", "clip",
]

# Large raga name list for extraction
RAGA_NAMES = [
    "kalyani", "bhairavi", "hindolam", "kharaharapriya", "mohanam",
    "shankarabharanam", "todi", "bhairav", "yaman", "durga",
    "madhyamavati", "hamsadhwani", "revati", "kambhoji", "natabhairavi",
    "charukesi", "simhendramadhyama", "hemavati", "dharmavati",
    "gamanasrama", "ritigowla", "suddhasaveri", "malkauns", "bageshri",
    "bilahari", "saurashtra", "nattai", "varali", "punnagavarali",
    "sahana", "anandabhairavi", "begada", "saveri", "kedaram",
    "harikambhoji", "arabhi", "panthuvarali", "mukhari", "vasanta",
    "sriranjani", "desh", "sindhu bhairavi", "mand", "kirwani",
    "jayantasri", "devagandhari", "nalinakanti", "nilambari", "lathangi",
    "sucharitra", "rasikapriya", "mechakalyani", "kiravani", "gaurimanohari",
    "natakuranji", "abhogi", "amritavarshini", "bagesri", "darbari",
    "suddhadhanyasi", "bowli", "kokilapriya", "gourimanohari",
]


# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

@dataclass
class RouterResult:
    mode: str                        # "theory" | "music" | "hybrid"
    wants_audio: bool = False
    raga_name: str | None = None     # extracted raga if detected
    theory_filters: list = field(default_factory=list)   # FAISS metadata filters
    music_filters: list = field(default_factory=list)    # FAISS metadata filters
    top_k_theory: int = 5
    top_k_music: int = 5


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def route_query(query: str) -> RouterResult:
    """
    Analyse the query and return a RouterResult that tells retrieval.py
    where to search and how many results to fetch from each index.
    """
    q = query.strip().lower()

    # --- extract raga name ---
    detected_raga = _extract_raga(q)

    # --- check audio intent ---
    wants_audio = any(phrase in q for phrase in AUDIO_TRIGGER_PHRASES)

    # --- score each mode ---
    theory_score = sum(1 for phrase in THEORY_TRIGGER_PHRASES if phrase in q)
    music_score = sum(1 for phrase in MUSIC_TRIGGER_PHRASES if phrase in q)

    # Hard overrides: explicit song/composer/list → music only
    if _is_explicit_music_query(q):
        mode = "music"
    # Hard overrides: audio-only with raga name → hybrid (need theory + audio)
    elif wants_audio and detected_raga:
        mode = "hybrid"
    # Theory question patterns
    elif theory_score > 0 and music_score == 0:
        mode = "theory"
    # Music question patterns
    elif music_score > 0 and theory_score == 0:
        mode = "music"
    # Both signals present
    elif theory_score > 0 and music_score > 0:
        mode = "hybrid"
    # Default: theory (safer for knowledge questions)
    else:
        mode = "theory"

    # Build FAISS type filters
    theory_filters = ["theory", "research"] if mode in ("theory", "hybrid") else []
    music_filters = ["music"] if mode in ("music", "hybrid") else []

    # Adjust top_k based on mode
    top_k_theory = 5 if mode in ("theory", "hybrid") else 0
    top_k_music = 5 if mode in ("music", "hybrid") else 0

    return RouterResult(
        mode=mode,
        wants_audio=wants_audio,
        raga_name=detected_raga,
        theory_filters=theory_filters,
        music_filters=music_filters,
        top_k_theory=top_k_theory,
        top_k_music=top_k_music,
    )


def _is_explicit_music_query(q: str) -> bool:
    """Return True if the query is clearly asking for song/dataset information."""
    patterns = [
        r"\blist\s+(?:of\s+)?songs\b",
        r"\bsongs\s+(?:by|of|in)\b",
        r"\bcompositions?\s+(?:by|of)\b",
        r"\bwho\s+composed\b",
        r"\bcomposed\s+by\b",
        r"\bvocalist\b",
        r"\bdiscography\b",
    ]
    return any(re.search(pat, q) for pat in patterns)


def _extract_raga(q: str) -> str | None:
    """Return the raga name found in the query, or None."""
    for raga in RAGA_NAMES:
        # word-boundary match, allow plural / possessive
        pattern = r"\b" + re.escape(raga) + r"(?:s|'s)?\b"
        if re.search(pattern, q, re.I):
            return raga.title()
    return None


# ---------------------------------------------------------------------------
# Utility: pretty-print route (for logging)
# ---------------------------------------------------------------------------

def describe_route(result: RouterResult) -> str:
    parts = [f"mode={result.mode}"]
    if result.raga_name:
        parts.append(f"raga={result.raga_name}")
    if result.wants_audio:
        parts.append("wants_audio=True")
    parts.append(f"top_k_theory={result.top_k_theory}")
    parts.append(f"top_k_music={result.top_k_music}")
    return " | ".join(parts)
