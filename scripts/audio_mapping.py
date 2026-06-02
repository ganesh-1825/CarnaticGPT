"""
audio_mapping.py
Carnatic GPT – Dynamic raga-to-audio mapping.
Scans audio/ folder at startup, builds a lookup table, and
resolves which audio files to serve for a given raga name.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

AUDIO_ROOT = Path("data/audio")

# Audio file types we serve, in priority order
AUDIO_EXTENSIONS = [".mp3", ".wav", ".ogg", ".flac"]

# Standard audio types we look for inside each raga folder
AUDIO_TYPE_PATTERNS = {
    "alapana": re.compile(r"alapana", re.IGNORECASE),
    "arohana": re.compile(r"aroha(na)?", re.IGNORECASE),
    "avarohana": re.compile(r"avaroha(na)?", re.IGNORECASE),
    "kriti": re.compile(r"kriti", re.IGNORECASE),
    "sample": re.compile(r"sample|demo|preview", re.IGNORECASE),
}


# ─────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────
class RagaAudio:
    def __init__(self, raga_name: str, folder: Path):
        self.raga_name = raga_name
        self.folder = folder
        self.files: Dict[str, str] = {}   # type → relative URL path

    def to_dict(self) -> Dict:
        return {
            "raga": self.raga_name,
            "audio_files": self.files,
            "available_types": list(self.files.keys()),
        }


# ─────────────────────────────────────────────
# SCANNER
# ─────────────────────────────────────────────
class AudioMapper:
    def __init__(self):
        self._map: Dict[str, RagaAudio] = {}   # lowercase raga name → RagaAudio
        self._loaded = False

    def _normalize_raga_name(self, name: str) -> str:
        return name.lower().strip().replace(" ", "_").replace("-", "_")

    def load(self):
        if self._loaded:
            return
        if not AUDIO_ROOT.exists():
            print(f"[AudioMapper] Audio root not found: {AUDIO_ROOT}")
            self._loaded = True
            return

        for raga_dir in sorted(AUDIO_ROOT.iterdir()):
            if not raga_dir.is_dir():
                continue
            raga_name = raga_dir.name
            raga_audio = RagaAudio(raga_name, raga_dir)

            for audio_file in sorted(raga_dir.iterdir()):
                if audio_file.suffix.lower() not in AUDIO_EXTENSIONS:
                    continue
                # Classify the file
                classified = False
                for audio_type, pattern in AUDIO_TYPE_PATTERNS.items():
                    if pattern.search(audio_file.stem):
                        raga_audio.files[audio_type] = f"audio/{raga_name}/{audio_file.name}"
                        classified = True
                        break
                if not classified:
                    # Use filename stem as key
                    raga_audio.files[audio_file.stem.lower()] = (
                        f"audio/{raga_name}/{audio_file.name}"
                    )

            key = self._normalize_raga_name(raga_name)
            self._map[key] = raga_audio

        self._loaded = True
        print(f"[AudioMapper] Loaded {len(self._map)} ragas: {', '.join(sorted(self._map.keys()))}")

    def get_audio(self, raga_name: str) -> Optional[Dict]:
        self.load()
        key = self._normalize_raga_name(raga_name)
        if key in self._map:
            return self._map[key].to_dict()

        # Fuzzy fallback: check if query is a substring of any key
        for stored_key, raga_audio in self._map.items():
            if key in stored_key or stored_key in key:
                return raga_audio.to_dict()

        return None

    def all_ragas(self) -> List[str]:
        self.load()
        return sorted(r.raga_name for r in self._map.values())

    def get_specific_file(self, raga_name: str, audio_type: str) -> Optional[str]:
        """Return URL path for a specific audio type within a raga."""
        data = self.get_audio(raga_name)
        if data is None:
            return None
        return data["audio_files"].get(audio_type.lower())

    def resolve_from_query(self, query: str) -> Optional[Dict]:
        """
        Extract raga name from a natural language query and return audio data.
        E.g.  "Play Kalyani alapana"  → Kalyani audio dict
        """
        self.load()
        query_lower = query.lower()
        # Try each known raga
        best_match: Optional[Dict] = None
        best_len = 0
        for key, raga_audio in self._map.items():
            raga_norm = self._normalize_raga_name(raga_audio.raga_name)
            if raga_norm in query_lower.replace(" ", "_"):
                if len(raga_norm) > best_len:
                    best_len = len(raga_norm)
                    best_match = raga_audio.to_dict()
        return best_match


# ─────────────────────────────────────────────
# SINGLETON & PUBLIC API
# ─────────────────────────────────────────────
_mapper = AudioMapper()


def get_raga_audio(raga_name: str) -> Optional[Dict]:
    return _mapper.get_audio(raga_name)


def resolve_audio_from_query(query: str) -> Optional[Dict]:
    return _mapper.resolve_from_query(query)


def list_available_ragas() -> List[str]:
    return _mapper.all_ragas()


def get_audio_file(raga_name: str, audio_type: str = "alapana") -> Optional[str]:
    return _mapper.get_specific_file(raga_name, audio_type)


# ─────────────────────────────────────────────
# CLI TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Available ragas:", list_available_ragas())
    for test_raga in ["Kalyani", "Hindolam", "Bhairavi", "kalyani", "HINDOLAM"]:
        result = get_raga_audio(test_raga)
        print(f"\nRaga: {test_raga}")
        if result:
            print(f"  Files: {result['audio_files']}")
        else:
            print("  Not found")

    print("\nQuery resolution:")
    for q in ["Play Kalyani audio", "Listen to Hindolam alapana", "Play Bhairavi sample"]:
        r = resolve_audio_from_query(q)
        print(f"  Q: {q}")
        print(f"  → {r}")
