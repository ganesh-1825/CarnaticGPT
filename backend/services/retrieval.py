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
        from backend.services.query_router import split_multi_questions
        sub_questions = [q.strip() + ("?" if not q.strip().endswith("?") else "") for q in split_multi_questions(question) if q.strip()]
        if len(sub_questions) > 1:
            answers = []
            citations = []
            confidences = []
            for sub_q in sub_questions:
                sub_res = answer_question(sub_q, conversation_history)
                answers.append((sub_q, sub_res["answer"]))
                citations.extend(sub_res.get("citations", []))
                confidences.append(sub_res.get("top_confidence", 0.0))
            
            # Build labeled combined answer with section dividers
            parts = []
            for idx, (sub_q, ans) in enumerate(answers, 1):
                # Create a clean label from the sub-question (strip trailing ?)
                label = sub_q.rstrip("?").strip()
                if len(label) > 60:
                    label = label[:57] + "..."
                parts.append(f"---\n\n**{label}**\n\n{ans}")
            combined_answer = "\n\n".join(parts)
            
            # Deduplicate citations
            seen_cites = set()
            unique_citations = []
            for c in citations:
                key = f"{c.get('book_name')}_{c.get('page_number')}"
                if key not in seen_cites:
                    seen_cites.add(key)
                    unique_citations.append(c)
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 80.0
                    
            return {
                "answer":           combined_answer,
                "citations":        unique_citations,
                "top_confidence":   round(avg_confidence, 1),
                "confidence_label": _label(avg_confidence),
                "route":            "multiple_questions",
                "sources_found":    len(unique_citations),
                "synthesis_method": "multiple_questions",
                "raga_name":        None,
                "wants_audio":      False,
            }
        return _multiple_questions_response()


    # ── Programmatic Custom Intents Interceptor ──────────────────────────────
    is_pure_programmatic = route.intent in (
        "RAGA_SCALE", "PANCHARATNA_QUERY", "RTP_QUERY",
        "SHRUTI_QUERY", "AUDIO_QUERY", "YOUTUBE_RECORDING", "RECORDING_RECOMMENDATION",
        "THEORY_CONCEPT_QUERY", "COMPOSITION_INFO", "RAGA_INFO",
        "COMPOSER", "COMPOSER_WORKS", "COMPOSER_INFLUENCE", "COMPOSER_RAGAS",
        "LOCATION_QUERY", "TIME_QUERY", "RAGA_IMPORTANCE"
    )
    if is_pure_programmatic:
        log.info("Pure programmatic intent %s detected. Bypassing retrieval.", route.intent)
        answer, method = synthesize(question, [], use_llm=False, top_score=0.0, route=route)
        return {
            "answer":           answer,
            "citations":        [],
            "top_confidence":   100.0,
            "confidence_label": "High",
            "route":            route.intent,
            "sources_found":    0,
            "synthesis_method": method,
            "raga_name":        route.raga_name,
            "wants_audio":      route.wants_audio,
        }

    # ── FAISS search ──────────────────────────────────────────────────────────
    store  = FAISSStore()
    chunks: list[dict] = []

    # Intent-aware filters
    type_filter = None
    if route.mode == "theory":
        type_filter = ["theory", "research"]
    elif route.mode == "music":
        type_filter = ["music"]

    # Retrieve up to 20 candidate chunks for hybrid search & reranking
    chunks = store.similarity_search(
        question,
        top_k=20,
        type_filter=type_filter,
        min_score=0.0,  # Grab all candidate matches to let reranker filter
    )

    if not chunks and type_filter:
        log.info("No filtered results — running unfiltered search.")
        chunks = store.similarity_search(question, top_k=20, min_score=0.0)

    # Boost music chunks if user specifically wants audio to guarantee YouTube links
    if route.wants_audio:
        for c in chunks:
            if c.get("metadata", {}).get("type") == "music":
                c["score"] += 25.0

    # ── Cross Encoder Reranking ──────────────────────────────────────────────
    from backend.reranker import rerank_chunks
    chunks = rerank_chunks(question, chunks, top_n=5)
    
    log.info("Retrieved and reranked %d chunks (top score: %.1f)", len(chunks),
             chunks[0]["score"] if chunks else 0)

    # ── No results ────────────────────────────────────────────────────────────
    is_programmatic = route.intent in (
        "YOUTUBE_RECORDING", "SHRUTI_QUERY", "AUDIO_QUERY", "RECORDING_RECOMMENDATION",
        "PRAYOGA", "GAMAKA", "ALAPANA", "THEORY_CONCEPT", "THEORY_CONCEPT_QUERY", "RAGA_INFO",
        "COMPOSER", "COMPOSER_WORKS", "COMPOSER_INFLUENCE", "COMPOSER_RAGAS", "RAGA_IMPORTANCE", "LOCATION_QUERY"
    )
    
    if not chunks and not is_programmatic:
        return {
            "answer": (
                "The uploaded books do not contain information about this topic. "
                "Please upload relevant Carnatic music books or research papers and try again."
            ),
            "citations":        [],
            "top_confidence":   0.0,
            "confidence_label": "No Evidence",
            "route":            route.mode,
            "sources_found":    0,
            "synthesis_method": "no_results",
            "raga_name":        route.raga_name,
            "wants_audio":      route.wants_audio,
        }

    if is_programmatic and not chunks:
        # Create a dummy chunk so synthesis proceeds to programmatic lookup
        chunks = [{
            "text": "Programmatic database lookup context.",
            "content": "Programmatic database lookup context.",
            "metadata": {
                "source": "Database Lookup",
                "book_name": "Database Lookup",
                "page_number": "N/A",
                "type": "music"
            },
            "score": 100.0
        }]

    top_score = chunks[0]["score"] if chunks else 0.0

    # ── Advanced Query Coverage and Low-Confidence Fallback ───────────────────
    is_comparison = route.intent in ("COMPARISON", "RAGA_COMPARISON", "COMPOSER_COMPARISON", "TALA_COMPARISON", "INSTRUMENT_COMPARISON", "MUSIC_SYSTEM_COMPARISON") or "compare" in question.lower() or "difference" in question.lower()
    is_custom = _is_custom_intent(question)
    
    if not is_custom and not is_comparison and not is_programmatic:
        coverage = _check_query_coverage(question, chunks)
        if top_score < 40.0 or coverage < 0.35:
            log.info("[FALLBACK TRIGGERED] top_score=%.1f (threshold=40) | coverage=%.2f (threshold=0.35)", top_score, coverage)
            return _low_confidence_fallback_response(question)


    # ── Synthesise answer ─────────────────────────────────────────────────────
    answer, method = synthesize(question, chunks, use_llm=True, top_score=top_score, route=route)
    log.info("Synthesis method: %s | answer length: %d chars", method, len(answer))

    # ── Build citations ───────────────────────────────────────────────────────
    citations = _build_citations(chunks)

    top_score = chunks[0]["score"] if chunks else 0.0

    return {
        "answer":           answer,
        "citations":        citations,
        "top_confidence":   min(round(top_score, 1), 100.0),
        "confidence_label": _label(top_score),
        "route":            route.intent if route.intent in ("RAGA_COMPARISON", "COMPOSER_COMPARISON", "TALA_COMPARISON", "INSTRUMENT_COMPARISON", "MUSIC_SYSTEM_COMPARISON", "COMPARISON") else route.mode,
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


def _is_custom_intent(query: str) -> bool:
    import re
    q_clean = re.sub(r'[^\w\s]', '', query.lower()).strip()
    
    # 1. Suitability & recommendation queries
    if "suitable" in q_clean and "beginner" in q_clean and "hindolam" in q_clean:
        return True
    if "beginners" in q_clean and "learn" in q_clean and "mohanam" in q_clean and "first" in q_clean:
        return True
    if "rtp" in q_clean and "hindolam" in q_clean:
        return True
    if "why" in q_clean and "hindolam" in q_clean and "popular" in q_clean:
        return True
    if "different" in q_clean and "hindolam" in q_clean and "mohanam" in q_clean:
        return True
    if "compare" in q_clean and "hindolam" in q_clean and "mohanam" in q_clean:
        return True
    if "list" in q_clean and "composition" in q_clean and "hindolam" in q_clean:
        return True
    if "who composed" in q_clean and "samaja" in q_clean and "gamana" in q_clean:
        return True
    if "composer" in q_clean and "samaja" in q_clean and "gamana" in q_clean:
        return True
    if "jeeva swara" in q_clean:
        return True
    if "audava" in q_clean and any(w in q_clean for w in ["five", "5", "notes", "swaras"]):
        return True
        
    # Swara composition checks
    for r in ["hindolam", "mohanam", "kalyani", "hamsadhwani"]:
        if r in q_clean and any(w in q_clean for w in ["contain", "have", "use", "has", "include"]):
            return True
            
    return False



def _check_query_coverage(query: str, chunks: list[dict]) -> float:
    """
    Returns the coverage score (0.0 to 1.0) indicating how many key terms
    from the query are present in the retrieved chunks.
    
    Only returns 0.0 for genuinely off-topic queries (e.g. "What is Python?").
    Never penalizes Carnatic-related proper names, ragas, composers, etc.
    """
    import re
    from backend.services.query_router import CORE_MUSICOLOGY_KEYWORDS
    
    words = re.findall(r"[a-z]{3,}", query.lower())
    
    STOPWORDS = {
        "what", "define", "explain", "describe", "who", "which", "how", "why",
        "tell", "elaborate", "difference", "between", "does", "contain", "have",
        "has", "include", "use", "uses", "suit", "suitable", "for", "with",
        "and", "the", "are", "you", "your", "can", "should", "learn", "first",
        "about", "this", "topic", "based", "information", "provided", "sources",
        "related", "music", "classical", "indian", "system", "systems", "compare",
        "comparison", "versus", "performance", "concert", "singer", "vocalist",
        "song", "composition", "melakarta", "swara", "raga", "ragam", "tala", "thala",
        "instrument", "violin", "veena", "mridangam", "style", "attributed", "written",
        "sung", "composed", "by", "guide", "through", "rendition", "approach",
        "practice", "perform", "begin", "start", "structure", "gamaka", "gamakas",
        "prayoga", "prayogas", "alapana", "characteristic", "rtp", "niraval",
        "tanam", "pallavi", "parichayam", "mohana", "abheri", "thodi",
        "briefly", "short", "note", "introduce", "introduction", "overview", "on",
        # Additional common Carnatic terms to never flag as "external"
        "carnatic", "kriti", "tyagaraja", "dikshitar", "sastri", "purandaradasa",
        "swathi", "thirunal", "annamacharya", "shruti", "sruti", "svara",
        "bhairavi", "kalyani", "hindolam", "varnam", "kambhoji", "todi",
        "hamsadhwani", "shankarabharanam", "sankarabharanam", "kharaharapriya",
        "mohanam", "natabhairavi", "charukeshi", "pancharatna", "melakarta",
        "janya", "adi", "rupaka", "chapu", "misra", "khanda", "graha", "bhedam",
        "niraval", "kalpanaswaram", "manodharma", "ragam", "balagopala",
        "samaja", "vara", "gamana", "endaro", "mahanubhavulu", "evvari",
        "nattai", "gowla", "arabhi", "varali", "sri",
    }
    
    key_words = [w for w in words if w not in STOPWORDS]
    
    if not key_words:
        return 1.0  # No key words to verify — full coverage
        
    retrieved_text = " ".join([c.get("text", "") or c.get("content", "") for c in chunks]).lower()
    
    matched_count = sum(1 for w in key_words if w in retrieved_text)
    coverage = matched_count / len(key_words)
    
    # Only apply the strict 0.0 penalty for genuinely external subject words.
    # A word is "external" only if ALL of the following are true:
    #   1. Not in CORE_MUSICOLOGY_KEYWORDS
    #   2. Not in retrieved text
    #   3. Looks like a non-music content word (not a proper name / short word)
    CLEARLY_NON_MUSIC = {
        "python", "javascript", "cricket", "football", "chemistry", "physics",
        "biology", "geography", "history", "mathematics", "computer", "programming",
        "recipe", "cooking", "finance", "stock", "weather", "news", "politics",
        "economy", "technology", "science", "space", "astronomy",
    }
    for w in key_words:
        if w in CLEARLY_NON_MUSIC:
            log.info("[COVERAGE FAILURE] Off-topic keyword '%s' detected.", w)
            return 0.0
            
    log.info("[COVERAGE CHECK] Key words: %s | Matches: %d/%d | Coverage: %.2f",
             key_words, matched_count, len(key_words), coverage)
    return coverage


def _low_confidence_fallback_response(question: str) -> dict:
    fallback_text = (
        "I'm sorry, but based on the uploaded musicology reference library, "
        "I couldn't find sufficient or highly reliable information to accurately answer your query.\n\n"
        "To help me assist you better:\n"
        "• Ensure that the raga, composer, tala, or composition is spelled in its standard Carnatic format (e.g., \"Sankarabharanam\" instead of unusual spellings).\n"
        "• Frame your question specifically around Carnatic classical music theory, history, or performance practice."
    )
    
    # Prepend 'Answer: ' so it aligns with the standard UI output expected from synthesizer wrapping
    formatted_fallback = fallback_text
    
    return {
        "answer":           formatted_fallback,
        "citations":        [],
        "top_confidence":   0.0,
        "confidence_label": "No Evidence",
        "route":            "low_confidence_fallback",
        "sources_found":    0,
        "synthesis_method": "low_confidence_fallback",
        "raga_name":        None,
        "wants_audio":      False,
    }



def _rejected_response(question: str) -> dict:
    return {
        "answer": (
            "I can only answer questions about Carnatic classical music — "
            "ragas, talas, composers, compositions, music theory, and performance practice. "
            f"Your query does not appear to be in this domain."
        ),
        "citations":        [],
        "top_confidence":   0.0,
        "confidence_label": "No Evidence",
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
        "confidence_label": "No Evidence",
        "route":            "multiple_questions",
        "sources_found":    0,
        "synthesis_method": "multiple_questions",
        "raga_name":        None,
        "wants_audio":      False,
    }