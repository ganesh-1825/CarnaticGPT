import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("DatabaseLoader")

# Path setup
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MASTER_DB_PATH = DATA_DIR / "master_carnatic_db.json"

# In-memory storage loaded once at startup
MASTER_DB = {}
RAGAS = []        # Melakarta-only (72 entries after cleanup)
TRACKS = []
ARTISTS = []
COMPOSERS = []
TALAS = []
SHRUTI = {}
PANCHARATNA = []

# ── Digital Gurukul canonical stats (shown in Dashboard / Library / Stats) ──
DIGITAL_GURUKUL_STATS = {
    "total_ragas":     72,       # 72 Melakarta ragas
    "indexed_books":   5,        # 5 curated reference texts
    "total_chunks":    15128,    # FAISS knowledge chunks
    "knowledge_base":  "Melakarta-72",
}

# Alternate raga spelling map
RAGA_ALIASES = {
    "shankarabharanam": "sankarabharanam",
    "dheerasankarabharanam": "sankarabharanam",
    # Todi / Hanuma Todi: DB stores this as 'Thodi' (Melakarta #8)
    "todi": "thodi",
    "hanuma todi": "thodi",
    "hanumatodi": "thodi",
    "hanumath todi": "thodi",
    # Kalyani: DB stores as 'Mechakalyani'
    "kalyani": "mechakalyani",
    "mechakalyani": "mechakalyani",
    "mecha kalyani": "mechakalyani",
    # Bhairavi: DB stores as 'Natabhairavi'
    "bhairavi": "natabhairavi",
    "natabhairavi": "natabhairavi",
    # Shubhapantuvarali alias
    "shubhapantuvarali": "shubhapantuvarali",
    "subhapantuvarali": "shubhapantuvarali",
    "pantuvarali": "shubhapantuvarali",
    # Sankarabharanam aliases
    "sankarabharanam": "sankarabharanam",
    # Kamboji
    "harikambhoji": "harikambhoji",
    "kamboji": "harikambhoji",
    # Hamsadhwani
    "hamsadwani": "hamsadhwani",
    "hamsadhvani": "hamsadhwani",
    # Misc
    "shuddha saveri": "shuddha_saveri",
    "suddhasaveri": "shuddha_saveri",
    "mohana": "mohanam",
}

def load_database():
    global MASTER_DB, RAGAS, TRACKS, ARTISTS, COMPOSERS, TALAS, SHRUTI, PANCHARATNA
    
    if not MASTER_DB_PATH.exists():
        logger.error(f"Master database not found at: {MASTER_DB_PATH}")
        return False
        
    try:
        with open(MASTER_DB_PATH, "r", encoding="utf-8") as f:
            MASTER_DB = json.load(f)
        
        # Load all ragas from file, then filter to Melakarta-only
        all_ragas = MASTER_DB.get("ragas", [])
        RAGAS = [
            r for r in all_ragas
            if r.get("type", "").lower() == "melakarta"
        ]
        
        # Preserve all other collections for composition/biography lookups
        TRACKS = MASTER_DB.get("tracks", [])
        ARTISTS = MASTER_DB.get("artists", [])
        COMPOSERS = MASTER_DB.get("composers", [])
        TALAS = MASTER_DB.get("talas", [])
        SHRUTI = MASTER_DB.get("shruti", {})
        PANCHARATNA = MASTER_DB.get("pancharatna", [])
        
        logger.info("Successfully loaded Master Carnatic Database (Digital Gurukul mode).")
        logger.info(
            f"Melakarta ragas: {len(RAGAS)} | Tracks: {len(TRACKS)} | "
            f"Composers: {len(COMPOSERS)} | Talas: {len(TALAS)}"
        )
        if len(RAGAS) != 72:
            logger.warning(
                f"Expected 72 Melakarta ragas, found {len(RAGAS)}. "
                "Run scratch/cleanup_melakarta_only.py to rebuild the database."
            )
        return True
    except Exception as e:
        logger.error(f"Error loading Master Carnatic Database: {e}")
        return False

# Centralized artist aliases cache
ARTIST_ALIASES = {}

def get_artist_aliases() -> dict:
    global ARTIST_ALIASES
    if ARTIST_ALIASES:
        return ARTIST_ALIASES
        
    core_abbrev = {
        "mss": "M. S. Subbulakshmi",
        "ms": "M. S. Subbulakshmi",
        "gnb": "G. N. Balasubramaniam",
        "mlv": "M. L. Vasanthakumari",
        "dkp": "D. K. Pattammal",
        "tmk": "T. M. Krishna",
        "tns": "T. N. Seshagopalan",
        "ariyakudi": "Ariyakudi Ramanuja Iyengar",
        "semmangudi": "Semmangudi Srinivasa Iyer",
        "lalgudi": "Lalgudi Jayaraman",
        "balamurali": "M. Balamuralikrishna",
    }
    
    aliases = {}
    for artist in ARTISTS:
        name = artist.get("name", "")
        if name:
            name_lower = name.lower()
            aliases[name_lower] = name
            for part in name_lower.split():
                part_clean = part.replace(".", "").replace(",", "").strip()
                if len(part_clean) > 3:
                    aliases[part_clean] = name
                    
    # Overlay core abbreviations
    for abbrev, full_name in core_abbrev.items():
        aliases[abbrev] = full_name
        
    ARTIST_ALIASES = aliases
    return ARTIST_ALIASES

# Self-initialize on import
load_database()
get_artist_aliases()

# ──────────────────────────────────────────────────────────────
# Lookup Functions
# ──────────────────────────────────────────────────────────────

def find_raga(name: str) -> dict | None:
    """Case-insensitive lookup for a Raga including common aliases."""
    if not name:
        return None
    name_clean = name.lower().strip()
    
    # Resolve aliases
    resolved_name = RAGA_ALIASES.get(name_clean, name_clean)
    
    for raga in RAGAS:
        if raga.get("name", "").lower() == resolved_name or raga.get("id", "").lower() == resolved_name:
            return raga
    return None

def find_artist(name: str) -> list:
    """Find tracks matching an artist/performer or composer name."""
    if not name:
        return []
    name_clean = name.lower().strip()
    
    matches = [
        track for track in TRACKS
        if name_clean in track.get("artist", "").lower() or name_clean in track.get("composer", "").lower()
    ]
    return matches

def find_recordings(raga_name: str) -> list:
    """Find tracks matching a specific Raga."""
    if not raga_name:
        return []
    
    raga_info = find_raga(raga_name)
    raga_canon = raga_info.get("name", raga_name).lower() if raga_info else raga_name.lower()
    
    matches = [
        track for track in TRACKS
        if track.get("ragam", "").lower() == raga_canon or track.get("ragam", "").lower() == raga_name.lower()
    ]
    return matches

def search_tracks(raga: str = None, artist: str = None, shruti: float = None) -> list:
    """Fuzzy filters tracks by raga, artist/performer name, and/or shruti kattai pitch."""
    results = TRACKS
    if raga:
        r_info = find_raga(raga)
        r_canon = r_info.get("name", raga).lower() if r_info else raga.lower()
        results = [t for t in results if t.get("ragam", "").lower() == r_canon or t.get("ragam", "").lower() == raga.lower()]
    if artist:
        a_clean = artist.lower().strip()
        results = [t for t in results if a_clean in t.get("artist", "").lower() or a_clean in t.get("composer", "").lower()]
    if shruti is not None:
        try:
            s_val = float(shruti)
            results = [t for t in results if abs(float(t.get("shruti_kattai", 0)) - s_val) < 0.1]
        except ValueError:
            pass
    return results

def find_composer(name: str) -> dict | None:
    """Case-insensitive composer biography lookup."""
    if not name:
        return None
    name_clean = name.lower().strip()
    
    # Check simple aliases/containments
    if "syama" in name_clean or "shyama" in name_clean:
        name_clean = "sastri"
    elif "thyagaraja" in name_clean:
        name_clean = "tyagaraja"
    elif "muthuswami" in name_clean:
        name_clean = "dikshitar"
    elif "swathi" in name_clean or "thirunal" in name_clean:
        name_clean = "swathi_thirunal"
        
    for composer in COMPOSERS:
        comp_name = composer.get("name", "").lower()
        comp_id = composer.get("id", "").lower()
        if (name_clean in comp_name or name_clean in comp_id or 
            comp_name in name_clean or comp_id in name_clean):
            return composer
    return None

def find_tala(name: str) -> dict | None:
    """Case-insensitive Tala lookup."""
    if not name:
        return None
    name_clean = name.lower().strip()
    
    for tala in TALAS:
        if name_clean in tala.get("name", "").lower():
            return tala
    return None

def find_shruti(kattai: str) -> str | None:
    """Pitch lookup using the kattai/shruti numbers."""
    if not kattai:
        return None
    # Support both pure key and fractional keys
    key = kattai.strip()
    return SHRUTI.get(key)

def find_pancharatna(query: str = "") -> list:
    """Get the full pancharatna list or filter by raga/order."""
    if not query:
        return PANCHARATNA
        
    query_clean = query.lower().strip()
    matches = []
    for kriti in PANCHARATNA:
        if (query_clean in kriti.get("song", "").lower() or 
            query_clean in kriti.get("raga", "").lower() or
            query_clean in kriti.get("language", "").lower()):
            matches.append(kriti)
    return matches if matches else PANCHARATNA
