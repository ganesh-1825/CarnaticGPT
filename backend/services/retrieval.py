"""
retrieval.py  —  FAISS retrieval + synthesis pipeline (FIXED)
=============================================================
Drop this into:  scripts/retrieval.py
             OR  backend/services/retrieval.py

Fixes:
  • Calls synthesize() and validates output — never returns raw OCR text
  • Falls back to rule_based_summary if LLM unavailable / returns garbage
  • Correct confidence thresholds: <25=low  25-60=medium  >60=high
  • Audio-first routing for "play X" queries
  • All five citation fields populated: book_name, page_number,
    confidence, excerpt, source
"""

import os
import logging

log = logging.getLogger("retrieval")

MIN_SCORE = float(os.getenv("MIN_SCORE", "25.0"))

# ── Import FAISSStore (works from both scripts/ and backend/services/) ────────
def _imp(primary, fallbacks):
    import importlib
    for m in [primary] + fallbacks:
        try:
            return importlib.import_module(m)
        except ImportError:
            continue
    raise ImportError(f"Cannot import {primary}")

_fs_mod  = _imp("backend.services.faiss_store",   ["services.faiss_store",  "faiss_store"])
_qr_mod  = _imp("backend.services.query_router",  ["services.query_router", "query_router"])
_syn_mod = _imp("backend.services.synthesizer",   ["services.synthesizer",  "synthesizer", "scripts.synthesizer"])

FAISSStore       = _fs_mod.FAISSStore
route_query      = _qr_mod.route_query
describe_route   = _qr_mod.describe_route
synthesize       = _syn_mod.synthesize


# ═══════════════════════════════════════════════════════════════════════════════
# Confidence label
# ═══════════════════════════════════════════════════════════════════════════════

def _label(score: float) -> str:
    if score < 25:  return "low"
    if score < 60:  return "medium"
    return "high"


# ═══════════════════════════════════════════════════════════════════════════════
# Main pipeline
# ═══════════════════════════════════════════════════════════════════════════════

def answer_question(
    question: str,
    conversation_history: list[dict] | None = None,
) -> dict:
    """
    Full pipeline:
      1. Route query (domain check + intent)
      2. FAISS similarity search (typed filters)
      3. Re-rank by score, keep top 5
      4. synthesize() → natural language answer
      5. Build citations
      6. Return structured response

    Return schema:
    {
        answer:           str,
        citations:        list[dict],
        top_confidence:   float,
        confidence_label: str,
        route:            str,
        sources_found:    int,
        synthesis_method: str,
        raga_name:        str | None,
        wants_audio:      bool,
    }
    """
    history = conversation_history or []
    route   = route_query(question)
    log.info("Route: %s", describe_route(route))

    # ── Domain rejected ───────────────────────────────────────────────────────
    if route.mode == "multiple_questions":
        return _multiple_questions_response()
    if route.mode == "rejected":
        return _rejected_response(question)

    # ── FAISS search ──────────────────────────────────────────────────────────
    store  = FAISSStore()
    chunks: list[dict] = []

    if route.top_k_theory > 0 and route.theory_filters:
        chunks += store.similarity_search(
            question,
            top_k=route.top_k_theory,
            type_filter=route.theory_filters,
            min_score=MIN_SCORE,
        )

    if route.top_k_music > 0 and route.music_filters:
        chunks += store.similarity_search(
            question,
            top_k=route.top_k_music,
            type_filter=route.music_filters,
            min_score=MIN_SCORE,
        )

    # Fallback: unfiltered search
    if not chunks:
        log.info("No typed results — running unfiltered search.")
        chunks = store.similarity_search(question, top_k=5, min_score=MIN_SCORE)

    # Boost music chunks if user specifically wants audio to guarantee YouTube links
    if route.wants_audio:
        for c in chunks:
            if c.get("metadata", {}).get("type") == "music":
                c["score"] += 25.0

    # Re-rank and trim (keep up to 10 to ensure mix of theory and music in hybrid mode)
    chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)[:10]
    log.info("Retrieved %d chunks (top score: %.1f)", len(chunks),
             chunks[0]["score"] if chunks else 0)

    # ── No results ────────────────────────────────────────────────────────────
    if not chunks:
        return {
            "answer": (
                "The uploaded books do not contain information about this topic. "
                "Please upload relevant Carnatic music books or research papers and try again."
            ),
            "citations":        [],
            "top_confidence":   0.0,
            "confidence_label": "low",
            "route":            route.mode,
            "sources_found":    0,
            "synthesis_method": "no_results",
            "raga_name":        route.raga_name,
            "wants_audio":      route.wants_audio,
        }

    top_score = chunks[0]["score"] if chunks else 0.0

    # ── Synthesise answer ─────────────────────────────────────────────────────
    answer, method = synthesize(question, chunks, use_llm=True, top_score=top_score, route=route)
    log.info("Synthesis method: %s | answer length: %d chars", method, len(answer))

    # ── Build citations ───────────────────────────────────────────────────────
    citations = _build_citations(chunks)

    top_score = chunks[0]["score"] if chunks else 0.0

    return {
        "answer":           answer,
        "citations":        citations,
        "top_confidence":   round(top_score, 1),
        "confidence_label": _label(top_score),
        "route":            route.mode,
        "sources_found":    len(chunks),
        "synthesis_method": method,
        "raga_name":        route.raga_name,
        "wants_audio":      route.wants_audio,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _build_citations(chunks: list[dict]) -> list[dict]:
    seen:      set[str]   = set()
    citations: list[dict] = []

    for c in chunks:
        m    = c.get("metadata", {})
        book = m.get("book_name") or m.get("source", "Unknown")
        page = m.get("page_number", 0)
        key  = f"{book}_{page}"

        if key in seen:
            continue
        seen.add(key)

        raw_text = c.get("text") or c.get("content") or ""
        excerpt  = raw_text[:180].strip()
        if len(raw_text) > 180:
            # End at last complete word
            excerpt = raw_text[:180].rsplit(" ", 1)[0] + "…"

        citations.append({
            "book_name":        book,
            "page_number":      page,
            "confidence":       round(c["score"], 1),
            "confidence_label": _label(c["score"]),
            "excerpt":          excerpt,
            "source":           m.get("source", ""),
            "type":             m.get("type", "theory"),
            "category":         m.get("category", m.get("type", "theory")),
            "youtube_url":      m.get("youtube", ""),
            "shruti":           m.get("shruti", ""),
            "melakarta":        m.get("melakarta", ""),
            "composer":         m.get("composer", ""),
            "song":             m.get("song", ""),
            "raga":             m.get("raga", "")
        })

    return citations


def _rejected_response(question: str) -> dict:
    return {
        "answer": (
            "I can only answer questions about Carnatic classical music — "
            "ragas, talas, composers, compositions, music theory, and performance practice. "
            f"Your query does not appear to be in this domain."
        ),
        "citations":        [],
        "top_confidence":   0.0,
        "confidence_label": "rejected",
        "route":            "rejected",
        "sources_found":    0,
        "synthesis_method": "domain_filter",
        "raga_name":        None,
        "wants_audio":      False,
    }

def _multiple_questions_response() -> dict:
    return {
        "answer": "You've asked multiple questions. Please ask them one by one.",
        "citations":        [],
        "top_confidence":   0.0,
        "confidence_label": "rejected",
        "route":            "multiple_questions",
        "sources_found":    0,
        "synthesis_method": "multiple_questions",
        "raga_name":        None,
        "wants_audio":      False,
    }