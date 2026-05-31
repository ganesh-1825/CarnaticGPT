import os
import sys
import json
import numpy as np
import requests
from backend.config import settings
from backend.logger import logger
from backend.model_loader import get_cached_embedder
from backend.reranker import rerank_chunks
from backend.confidence_engine import calculate_confidence
from backend.response_generator import generate_natural_response
from backend.response_formatter import format_answer
from backend.query_optimizer import detect_query_type, extract_ragas, extract_raga
from backend.raga_knowledge_base import (
    RAGA_KNOWLEDGE_BASE, find_raga_key, get_raga_info, SUPPORTED_RAGA_NAMES
)
from backend.theory_knowledge_base import (
    find_theory_key, build_theory_chunk
)

# Ensure project root is visible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def optimize_query(query: str) -> str:
    """Optimizes the search query by sanitizing, removing questions markers,
    and expanding classic terms for better semantic vector retrieval.
    """
    cleaned = query.strip().rstrip('?').rstrip('.')
    query_lower = cleaned.lower()
    
    # Emotion synonym mapping query expansion for South Indian treatises
    emotion_map = {
        "compassion": ["karuna", "sadness", "emotion"],
        "devotion": ["bhakti", "spiritual"],
        "brightness": ["majestic", "adbhutam", "energy"],
        "joy": ["sweetness", "sringara", "playful"]
    }
    
    for key, synonyms in emotion_map.items():
        if key in query_lower:
            expansion = " " + " ".join(synonyms)
            cleaned = cleaned.replace(key, f"{key}{expansion}").replace(key.capitalize(), f"{key.capitalize()}{expansion}")
            query_lower = cleaned.lower()
    
    # Data-driven semantic expansion: add "Raga" prefix for any recognized raga name
    raga_key = find_raga_key(query)
    if raga_key and "raga" not in query_lower:
        raga_info = get_raga_info(raga_key)
        if raga_info:
            display_name = raga_info["name"]
            # Only add prefix if the raga name is in the query
            if display_name.lower() in query_lower:
                cleaned = cleaned.replace(display_name, f"Raga {display_name}")
            elif raga_key in query_lower:
                cleaned = cleaned.replace(raga_key, f"Raga {display_name}")
        
    return cleaned


def _build_raga_chunk(raga_key: str) -> dict:
    """Build a high-quality retrieval chunk from the knowledge base for a recognized raga."""
    info = get_raga_info(raga_key)
    if not info:
        return None
    
    # Build rich text from structured data
    name = info["name"]
    compositions_text = "; ".join([f"{c['name']} by {c['composer']}" for c in info["compositions"]])
    features_text = ". ".join(info["special_features"])
    hindustani = f" Its Hindustani music equivalent is {info['hindustani_equivalent']}." if info.get("hindustani_equivalent") else ""
    
    text = (
        f"Raga {name} is a {info['type']} raga of the {info['melakarta_name']} "
        f"(Melakarta {info['melakarta_number']}). "
        f"Arohana: {info['arohana']}. Avarohana: {info['avarohana']}. "
        f"It evokes {', '.join(info['rasas'])} rasas. "
        f"Best performed during {info['time']}.{hindustani} "
        f"Famous compositions include {compositions_text}. "
        f"{features_text}"
    )
    
    return {
        "chunk_id": f"kb_{raga_key}_main",
        "text": text,
        "source": "Knowledge_Base/raga_knowledge_base.py",
        "book_name": "CarnaticGPT Raga Knowledge Base",
        "page": info["melakarta_number"],
        "score": 0.95
    }


# Module-level FAISS cache to prevent HuggingFace client from being closed between queries
_faiss_cache = {"db": None, "embeddings": None}

def _get_faiss_db():
    # Deprecated: now we use FAISSStore singleton
    return None

from backend.services.faiss_store import FAISSStore

def retrieve_top_chunks(query: str, k: int = 5, query_type: str = "all") -> list:
    """Searches the vector indexing metadata for segments matching the query, retrieving up to k chunks using FAISSStore."""
    try:
        store = FAISSStore()
    except Exception as e:
        logger.warning(f"FAISSStore loading failed: {e}. Returning mock retrievals.")
        return get_mock_retrievals(query)
        
    if store.index.ntotal == 0:
        logger.warning("FAISSStore index is empty. Returning mock retrievals.")
        return get_mock_retrievals(query)

    try:
        # Data-driven injection: if query mentions a known raga, inject its KB chunk first
        raga_key = find_raga_key(query)
        results = []
        if raga_key:
            kb_chunk = _build_raga_chunk(raga_key)
            if kb_chunk:
                results.append(kb_chunk)
        
        # Data-driven injection: if query mentions a known theory concept, inject its definition
        theory_key = find_theory_key(query)
        if theory_key:
            theory_chunk = build_theory_chunk(theory_key)
            if theory_chunk:
                logger.info(f"Injecting theory KB chunk for concept: '{theory_key}'")
                results.append(theory_chunk)
                
        type_filter = None
        if query_type == "theory":
            type_filter = ["theory", "research"]
        elif query_type == "music":
            type_filter = ["music"]
            
        search_results = store.similarity_search(query, top_k=k, type_filter=type_filter, min_score=0.0)
        
        # If filtered search returns nothing, fall back to unfiltered search
        if not search_results and type_filter:
            logger.info(f"Filtered search returned 0 results. Falling back to unfiltered search.")
            search_results = store.similarity_search(query, top_k=k, min_score=0.0)

        for idx, res in enumerate(search_results):
            meta = res["metadata"]
            # Convert 0-100 score to 0.0-1.0
            score = res["score"] / 100.0
            
            # Avoid duplicating if we already injected a KB chunk for this raga
            if raga_key:
                rec_text_lower = res["text"].lower()
                if raga_key in rec_text_lower:
                    continue
                    
            results.append({
                "chunk_id": meta.get("id", f"chunk_{idx}"),
                "text": res["text"],
                "source": meta.get("source", "CarnaticSongsDatabase.csv"),
                "book_name": meta.get("book_name", "Music Dataset"),
                "page": meta.get("page_number", 1),
                "score": score
            })
        return results
    except Exception as e:
        logger.error(f"Vector search failed: {e}. Falling back to keyword search.")
        return keyword_fallback_search(query, k)

def get_mock_retrievals(query: str) -> list:
    """Data-driven mock retrieval using the knowledge base for any of the 30 supported ragas."""
    query_lower = query.lower()
    
    # Check if query mentions any known raga
    raga_key = find_raga_key(query)
    if raga_key:
        kb_chunk = _build_raga_chunk(raga_key)
        if kb_chunk:
            return [kb_chunk]
    
    # Emotion-based queries
    if "compassion" in query_lower or "karuna" in query_lower:
        chunk = _build_raga_chunk("bhairavi")
        if chunk:
            return [chunk]
    
    # Default fallback
    return [
        {
            "chunk_id": "raga_lakshana_p1_c1",
            "text": "Raga Mayamalavagowla is the 15th Melakarta raga in the Katapayadi scheme. Arohana: S R1 G3 M1 P D1 N3 S. Avarohana: S N3 D1 P M1 G3 R1 S. Symmetrical and uniform semitone spaces make it the baseline standard for Carnatic beginners.",
            "source": "Ragas/Raga_Lakshana.txt",
            "book_name": "Raga Lakshana",
            "page": 1,
            "score": 0.8845
        },
        {
            "chunk_id": "south_indian_p2_c1",
            "text": "The primary melodic instruments are the Veena, Violin, and Flute. The main percussion is the Mridangam. Rhythms are structured using the Sapta Tala system, which includes seven base rhythmic cycles like Adi Tala (8 beats).",
            "source": "South_Indian_Music/South_Indian_Book5.txt",
            "book_name": "South Indian Book 5",
            "page": 2,
            "score": 0.7412
        }
    ]

def keyword_fallback_search(query: str, k: int = 10) -> list:
    """Simple text keyword similarity fallback search using FAISSStore metadata."""
    try:
        store = FAISSStore()
        metadata = store.metadata
    except Exception:
        return get_mock_retrievals(query)
        
    if not metadata:
        return get_mock_retrievals(query)
        
    query_words = set(query.lower().split())
    scored = []
    
    for item in metadata:
        text = item.get("content", "")
        chunk_words = set(text.lower().split())
        overlap = len(query_words.intersection(chunk_words))
        score = overlap / len(query_words) if query_words else 0.0
        scored.append((score, item))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    
    for score, item in scored[:k]:
        results.append({
            "chunk_id": item.get("id", ""),
            "text": item.get("content", ""),
            "source": item.get("source", ""),
            "book_name": item.get("book_name", ""),
            "page": item.get("page_number", 1),
            "score": max(0.5, score) # Cap at min 0.5 for ui representation
        })
    return results

import re

CARNATIC_KEYWORDS = [
    "raga", "ragam", "shruti", "swara", "talam", "tala", "composer", "tyagaraja", 
    "dikshitar", "syama sastri", "sastri", "kriti", "song", "melakarta", "arohana", 
    "avarohana", "gamaka", "carnatic", "hindolam", "kalyani", "mohanam", 
    "bhairavi", "abheri", "music", "musicology", "computational", "notation",
    "treatise", "classical", "swati", "tirunal", "purandaradasa", "shastra",
    "manuscript", "composition", "singing", "vocal", "instrument", "mridangam"
]

def validate_query(query: str) -> bool:
    query_lower = query.lower()
    # Remove symbols to isolate keywords cleanly
    sanitized = re.sub(r'[^a-zA-Z0-9 ]', '', query_lower)
    for word in CARNATIC_KEYWORDS:
        if word in sanitized:
            return True
    return False

from scripts.query_expand import expand_query
from backend.query_router import route_query

def execute_rag_pipeline(query: str) -> dict:
    """End-to-End Orchestrator for CarnaticGPT Search:
    User Question -> Intent Detection -> Query Optimizer -> Embeddings -> FAISS Multi-Entity Search 
    -> Reranker -> Top 3 -> Response Gen & Confidence evaluation
    """
    logger.info(f"Executing improved RAG Pipeline for query: '{query}'")
    
    # -2. Domain Restriction Check
    if not validate_query(query):
        logger.info(f"Query '{query}' rejected as outside CarnaticGPT knowledge domain.")
        return {
            "response": (
                "This question is outside the CarnaticGPT knowledge domain.\n\n"
                "Please ask questions related to:\n\n"
                "• Ragas\n"
                "• Composers\n"
                "• Songs\n"
                "• Shruti\n"
                "• Talam\n"
                "• Carnatic theory\n"
                "• Uploaded PDFs"
            ),
            "confidence": "Low Confidence",
            "citations": [],
            "detected_raga": None
        }

    # -1. Route Query
    query_type = route_query(query)
    
    # 0. Query Expansion
    query = expand_query(query)
    
    # 1. Query Optimizer / Intent Detection
    q_type = detect_query_type(query)
    optimized = optimize_query(query)
    detected_raga = extract_raga(query)
    
    # 2. Intent-Aware FAISS Retrieval
    if q_type == "comparison":
        ragas = extract_ragas(query)
        if ragas:
            r1, r2 = ragas["raga1"], ragas["raga2"]
            logger.info(f"Comparison query detected. Running independent retrievals for '{r1}' and '{r2}'")
            retrieved_r1 = retrieve_top_chunks(r1, k=5, query_type=query_type)
            retrieved_r2 = retrieve_top_chunks(r2, k=5, query_type=query_type)
            
            # Merge and deduplicate matches
            candidates = []
            seen_ids = set()
            for chunk in retrieved_r1 + retrieved_r2:
                if chunk["chunk_id"] not in seen_ids:
                    seen_ids.add(chunk["chunk_id"])
                    candidates.append(chunk)
        else:
            candidates = retrieve_top_chunks(optimized, k=10, query_type=query_type)
    else:
        candidates = retrieve_top_chunks(optimized, k=10, query_type=query_type)
        
    # Apply Query Entity Keyword Filter to eliminate retrieval drift
    if detected_raga:
        logger.info(f"Raga entity detected: '{detected_raga}'. Filtering retrieval matching keywords.")
        candidates = [
            chunk for chunk in candidates
            if detected_raga.lower() in chunk["text"].lower() or 
               detected_raga.lower() in chunk["source"].lower() or
               detected_raga.lower() in chunk["book_name"].lower()
        ]
        
    # 3. Rerank down to Top 3
    reranked_3 = rerank_chunks(optimized, candidates, top_n=3)
    
    # Check if this query matches any known raga or high-quality template
    has_custom_template = False
    query_lower = query.lower()
    
    # Data-driven: check against all supported ragas
    raga_key = find_raga_key(query)
    if raga_key:
        has_custom_template = True
    
    # Also check for special topic keywords
    special_keywords = ["tyagaraja", "quiz", "tala", "dikshitar", "prahalada", "vijayam"]
    if any(k in query_lower for k in special_keywords):
        has_custom_template = True
    if "pentatonic" in query_lower and ("shiva" in query_lower or "saivis" in query_lower or "shivan" in query_lower):
        has_custom_template = True

    # Get overall confidence
    overall_confidence_score = 0.0
    if reranked_3:
        overall_confidence_score = reranked_3[0]["score"]
        
    if has_custom_template:
        overall_confidence_score = max(overall_confidence_score, 0.96)

    # Enforce Relevance Threshold of 0.15 to block low-confidence hallucinated answers
    if not reranked_3 or overall_confidence_score < 0.15:
        return {
            "response": "Low confidence answer",
            "confidence": "Low Confidence",
            "detected_raga": detected_raga,
            "citations": []
        }
    
    # Generate final answer
    raw_response = generate_natural_response(query, reranked_3)
    response_text = format_answer(raw_response)
    
    # 4. Apply Confidence Classification to each citation
    for chunk in reranked_3:
        chunk["confidence"] = calculate_confidence(chunk["score"])
        
    return {
        "response": response_text,
        "confidence": calculate_confidence(overall_confidence_score),
        "citations": reranked_3,
        "detected_raga": detected_raga
    }
