"""
retrieval.py  —  FAISS retrieval for standalone scripts/ pipeline.
Exposes:
  retrieve_chunks(query, top_k=5) -> dict with keys:
      context, chunks, route, top_confidence, raga_name, wants_audio
  build_context(query, top_k=5)   -> (context_str, retrieval_dict)

Confidence tiers: <25 = low  |  25-60 = medium  |  >60 = high
"""
import os
import re
import json
import logging
import numpy as np
from pathlib import Path

log = logging.getLogger("CarnaticGPT-Retrieval")

BASE_DIR       = Path(__file__).resolve().parent.parent
CHUNKS_FILE    = BASE_DIR / "data" / "chunks" / "cleaned_chunks.json"
FAISS_INDEX    = BASE_DIR / "data" / "vectorDB" / "index.faiss"
METADATA_FILE  = BASE_DIR / "data" / "vectorDB" / "metadata.json"
EMBEDDINGS_NPY = BASE_DIR / "data" / "vectorDB" / "embeddings.npy"

MIN_SCORE     = float(os.getenv("MIN_SCORE",     "25.0"))
TOP_K_DEFAULT = int(os.getenv("TOP_K",           "5"))

# ── lazy state ─────────────────────────────────────────────────────────────────
_faiss_index  = None
_metadata     = None
_embeddings   = None
_embedder     = None


# ══════════════════════════════════════════════════════════════════════════════
# LOAD
# ══════════════════════════════════════════════════════════════════════════════

def _load_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        log.info("Embedder loaded: all-MiniLM-L6-v2")
    except Exception as e:
        log.error("Could not load embedder: %s", e)
        _embedder = None
    return _embedder


def _load_index():
    global _faiss_index, _metadata, _embeddings
    if _faiss_index is not None:
        return True

    # ── FAISS path ─────────────────────────────────────────────────────────────
    if FAISS_INDEX.exists() and METADATA_FILE.exists():
        try:
            import faiss
            _faiss_index = faiss.read_index(str(FAISS_INDEX))
            with open(METADATA_FILE, encoding="utf-8") as f:
                _metadata = json.load(f)
            log.info("FAISS index loaded: %d vectors", _faiss_index.ntotal)
            return True
        except Exception as e:
            log.warning("FAISS load failed: %s", e)

    # ── numpy fallback ─────────────────────────────────────────────────────────
    if EMBEDDINGS_NPY.exists() and METADATA_FILE.exists():
        try:
            _embeddings = np.load(str(EMBEDDINGS_NPY))
            with open(METADATA_FILE, encoding="utf-8") as f:
                _metadata = json.load(f)
            log.info("NumPy embeddings loaded: %d vectors", len(_embeddings))
            return True
        except Exception as e:
            log.warning("NumPy load failed: %s", e)

    log.error("No vector index found. Run scripts/ingest.py first.")
    return False


# ══════════════════════════════════════════════════════════════════════════════
# SEARCH
# ══════════════════════════════════════════════════════════════════════════════

def _embed(text: str) -> np.ndarray:
    emb = _load_embedder()
    if emb is None:
        return np.zeros(384, dtype=np.float32)
    vec = emb.encode([text], normalize_embeddings=True)[0]
    return vec.astype(np.float32)


def _score_to_label(score: float) -> str:
    if score < 25:  return "low"
    if score < 60:  return "medium"
    return "high"


def _search(query: str, top_k: int, type_filter: list | None = None) -> list[dict]:
    if not _load_index():
        return []

    vec = _embed(query)
    results = []

    # ── FAISS search ───────────────────────────────────────────────────────────
    if _faiss_index is not None:
        import faiss
        q = vec.reshape(1, -1)
        faiss.normalize_L2(q)
        distances, indices = _faiss_index.search(q, top_k * 3)
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(_metadata):
                continue
            entry = _metadata[idx]
            score = float(dist) * 100        # inner-product on normalised vecs → 0-100
            if score < MIN_SCORE:
                continue
            if type_filter and entry.get("type") not in type_filter:
                continue
            results.append({**entry, "score": round(score, 1)})

    # ── NumPy cosine fallback ──────────────────────────────────────────────────
    elif _embeddings is not None:
        dots  = _embeddings @ vec
        norms = np.linalg.norm(_embeddings, axis=1) * (np.linalg.norm(vec) or 1e-9)
        sims  = dots / np.where(norms == 0, 1e-9, norms)
        top_i = np.argsort(sims)[::-1][: top_k * 3]
        for idx in top_i:
            entry = _metadata[idx]
            score = float(sims[idx]) * 100
            if score < MIN_SCORE:
                continue
            if type_filter and entry.get("type") not in type_filter:
                continue
            results.append({**entry, "score": round(score, 1)})

    return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]


# ══════════════════════════════════════════════════════════════════════════════
# QUERY ROUTER  (lightweight copy — avoids circular import with backend)
# ══════════════════════════════════════════════════════════════════════════════

_DOMAIN_KW = [
    "raga","ragam","tala","swara","shruti","gamaka","alapana","carnatic","karnatik",
    "music","song","kriti","varnam","pallavi","melapakarta","janya","arohana",
    "avarohana","composer","tyagaraja","dikshitar","bhairavi","kalyani","hindolam",
    "mohanam","todi","hamsadhwani","instrument","veena","mridangam","violin",
    "concert","bhakti","devotional","classical","what is","define","explain",
    "describe","who is","compare","audio","play","listen","hear","ghatam","flute",
    "kharaharapriya","shankarabharanam","charukesi","bilahari","abhogi","nattai",
    "saveri","anandabhairavi","arabhi","amritavarshini","sivaranjani","madhyamavati",
]
_AUDIO_KW  = {"play","listen","audio","hear","sample","alapana","clip"}
_MUSIC_KW  = {"song","songs","list","compositions","composed","composer","vocalist",
               "performer","singer","recording","kriti","keerthana","popular","famous"}
_THEORY_KW = {"what","define","explain","describe","how","difference","compare",
               "types","characteristics","origin","history","significance","meaning"}

_RAGA_LIST = [
    "kalyani","bhairavi","hindolam","kharaharapriya","mohanam","shankarabharanam",
    "todi","hamsadhwani","revati","madhyamavati","bilahari","natabhairavi","charukesi",
    "saveri","suddhasaveri","kambhoji","anandabhairavi","nattai","abhogi","arabhi",
    "amritavarshini","sivaranjani","hamsanadam","keeravani","bhupalam","bilahari",
    "darbari","desh","yaman","malkouns","bageshri","mayamalavagowla",
]


def _route(query: str) -> dict:
    lower = query.lower()
    tokens = set(re.findall(r"\b\w+\b", lower))

    # Domain gate
    if not any(kw in lower for kw in _DOMAIN_KW):
        return {"mode": "rejected", "raga_name": None, "wants_audio": False}

    raga = next((r.title() for r in _RAGA_LIST
                 if re.search(r"\b" + re.escape(r) + r"s?\b", lower)), None)
    wants_audio = bool(tokens & _AUDIO_KW)
    m_score     = len(tokens & _MUSIC_KW)
    t_score     = len(tokens & _THEORY_KW)

    if wants_audio and raga:
        mode = "hybrid"
    elif re.search(r"\b(list|show|find|songs?|compositions?|who\s+composed)\b", lower):
        mode = "music"
    elif m_score > t_score:
        mode = "music"
    elif t_score >= m_score:
        mode = "theory"
    else:
        mode = "hybrid"

    return {"mode": mode, "raga_name": raga, "wants_audio": wants_audio}


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def retrieve_chunks(query: str, top_k: int = TOP_K_DEFAULT) -> dict:
    """
    Full retrieval pipeline.
    Returns dict with: context, chunks, route, top_confidence, raga_name, wants_audio
    """
    route_info = _route(query)
    mode       = route_info["mode"]

    if mode == "rejected":
        return {
            "context":        "",
            "chunks":         [],
            "route":          "rejected",
            "top_confidence": 0.0,
            "raga_name":      None,
            "wants_audio":    False,
        }

    chunks: list[dict] = []

    if mode in ("theory", "hybrid"):
        chunks += _search(query, top_k, type_filter=["theory", "research"])
    if mode in ("music", "hybrid"):
        chunks += _search(query, top_k, type_filter=["music"])
    if not chunks:
        chunks = _search(query, top_k)   # unfiltered fallback

    # Deduplicate & keep best top_k
    seen: set[str] = set()
    unique: list[dict] = []
    for c in sorted(chunks, key=lambda x: x["score"], reverse=True):
        key = (c.get("text", c.get("content", "")) or "")[:80]
        if key not in seen:
            seen.add(key)
            unique.append(c)
        if len(unique) >= top_k:
            break
    chunks = unique

    # Build context string for LLM
    ctx_parts = []
    for i, c in enumerate(chunks, 1):
        text  = c.get("text", c.get("content", ""))
        score = c.get("score", 0)
        src   = c.get("source", "KB")
        ctx_parts.append(f"[Source {i} | {src} | relevance {score:.0f}%]\n{text}")
    context = "\n\n---\n\n".join(ctx_parts)

    top_conf = chunks[0]["score"] if chunks else 0.0

    return {
        "context":        context,
        "chunks":         chunks,
        "route":          mode,
        "top_confidence": round(top_conf, 1),
        "raga_name":      route_info["raga_name"],
        "wants_audio":    route_info["wants_audio"],
    }


def build_context(query: str, top_k: int = TOP_K_DEFAULT) -> tuple[str, dict]:
    """Backwards-compatible helper returning (context_str, retrieval_dict)."""
    r = retrieve_chunks(query, top_k)
    return r["context"], r