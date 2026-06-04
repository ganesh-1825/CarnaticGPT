import re
import math
import logging
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def is_administrative_chunk(text: str) -> bool:
    text_lower = text.lower()
    admin_keywords = [
        "syllabus", "course outline", "lesson plan", "module", "study hours", 
        "exam metadata", "administrative", "curriculum", "marks distribution", 
        "credit hours", "question paper", "assignment", "semester", "enrolment", 
        "instructional hours", "module distribution", "exam pattern", "study plans",
        "reference books", "grading scheme", "lecture schedule", "recommended books",
        "units", "unit i", "unit ii", "unit iii", "unit iv", "unit v"
    ]
    for kw in admin_keywords:
        if kw in text_lower:
            return True
    return False

def classify_chunk_tag(text: str, meta: dict) -> str:
    text_lower = text.lower()
    
    # 1. administration / exam
    if is_administrative_chunk(text):
        if any(k in text_lower for k in ["exam", "marks", "grade", "assignment", "question paper"]):
            return "exam"
        return "administration"
        
    # 2. raga
    raga_keywords = ["raga", "ragam", "arohana", "avarohana", "swara", "melakarta", "janya", "scale", "sanchara", "prayoga"]
    # 3. composer
    composer_keywords = ["composer", "composed", "tyagaraja", "dikshitar", "syama", "purandaradasa", "shastri"]
    # 4. tala
    tala_keywords = ["tala", "talam", "beats", "akshara", "adi tala", "rupaka", "angas", " rhythmic"]
    # 5. history
    history_keywords = ["history", "evolution", "origin", "ancient", "century", "treatise", "historical", "sangeeta sampradaya"]
    
    if any(k in text_lower for k in composer_keywords):
        return "composer"
    if any(k in text_lower for k in tala_keywords):
        return "tala"
    if any(k in text_lower for k in history_keywords):
        return "history"
    if any(k in text_lower for k in raga_keywords):
        return "raga"
        
    return "theory"

class CarnaticReranker:
    """Reranks retrieved text chunks based on semantic similarity, exact term matches,
    and domain-specific keywords for Carnatic music, incorporating CrossEncoder or fallback metrics.
    """
    
    CARNATIC_BOOST_WORDS = [
        "bhairavi", "kalyani", "mohanam", "mayamalavagowla", "mayamalavagaula",
        "tyagaraja", "dikshitar", "sastry", "syama", "purandara",
        "tala", "raga", "swara", "gamaka", "sarali", "jantai", "alankaram",
        "mridangam", "veena", "violin", "flute", "sruthi", "shruti", "melakarta",
        "prahalada", "vijayam", "sanskrit", "telugu", "lakshana", "niraval", "rtp",
        "tanam", "pallavi", "graha bhedam", "modal shift"
    ]

    def __init__(self):
        self.cross_encoder = None
        try:
            from sentence_transformers import CrossEncoder
            # Load BAAI/bge-reranker-base cross-encoder model for CPU reranking as requested by user
            self.cross_encoder = CrossEncoder("BAAI/bge-reranker-base", device="cpu")
            logger.info("SentenceTransformers CrossEncoder (BAAI/bge-reranker-base) loaded successfully on CPU.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformers CrossEncoder ({e}). Using fallback scoring.")

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        """Reranks a list of retrieved chunks using a hybrid scoring algorithm and returns top_n."""
        if not chunks:
            return []
            
        logger.info(f"Reranking {len(chunks)} chunks for query: '{query}'")
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        # 1. First Pass: Tag chunks and filter/penalize noise
        is_admin_query = any(w in query_lower for w in ["syllabus", "course", "exam", "assignment", "marks", "reference", "distribution"])
        is_history_query = any(w in query_lower for w in ["history", "origin", "evolution", "ancient", "century"])
        
        filtered_chunks = []
        for chunk in chunks:
            text = chunk.get("text", "") or chunk.get("content", "")
            meta = chunk.get("metadata", chunk.get("metadata", {}))
            
            tag = classify_chunk_tag(text, meta)
            
            # Substantial penalty for administrative/exam chunks if it's not an admin query
            score_modifier = 0.0
            if tag in ("administration", "exam"):
                if not is_admin_query:
                    score_modifier = -45.0  # Heavy penalty to force it out of top results
                    
            # Boost history chunks for history queries
            if tag == "history" and is_history_query:
                score_modifier = 15.0
                
            new_chunk = dict(chunk)
            # Add metadata tags
            new_chunk["tag"] = tag
            new_chunk["score_modifier"] = score_modifier
            filtered_chunks.append(new_chunk)

        # 2. Second Pass: Score using CrossEncoder or Fallback
        if self.cross_encoder is not None:
            try:
                pairs = [[query, c.get("text", "") or c.get("content", "")] for c in filtered_chunks]
                raw_scores = self.cross_encoder.predict(pairs)
                if not isinstance(raw_scores, (list, np.ndarray)):
                    raw_scores = [raw_scores]
                
                # Check if we need to apply sigmoid (e.g. if any score is negative or > 1)
                needs_sigmoid = any(s < 0.0 or s > 1.0 for s in raw_scores)
                
                for i, score in enumerate(raw_scores):
                    if needs_sigmoid:
                        sig_score = 1.0 / (1.0 + math.exp(-score))
                    else:
                        sig_score = float(score)
                        
                    # Scale back to 0-100 range and apply modifiers
                    final_score = float(np.clip(sig_score * 100.0 + filtered_chunks[i]["score_modifier"], 1.0, 100.0))
                    filtered_chunks[i]["score"] = final_score
            except Exception as e:
                logger.error(f"CrossEncoder prediction failed: {e}. Falling back.")
                self._fallback_score(query_lower, query_words, filtered_chunks)
        else:
            self._fallback_score(query_lower, query_words, filtered_chunks)
            
        # Sort chunks by final score descending
        filtered_chunks.sort(key=lambda x: x["score"], reverse=True)
        logger.info(f"Top 5 reranked scores: {[round(c['score'], 1) for c in filtered_chunks[:top_n]]}")
        return filtered_chunks[:top_n]

    def _fallback_score(self, query_lower: str, query_words: set, chunks: List[dict]):
        for chunk in chunks:
            text_lower = (chunk.get("text", "") or chunk.get("content", "")).lower()
            text_words = set(re.findall(r'\w+', text_lower))
            
            # Base semantic score (ensure it is on a 0-100 scale)
            semantic_score = chunk.get("score", 50.0)
            if semantic_score <= 1.0:
                semantic_score *= 100.0
                
            # Keyword overlap score
            intersection = query_words.intersection(text_words)
            overlap_score = (len(intersection) / len(query_words) * 100.0) if query_words else 0.0
            
            # Domain-specific keyword boost
            boost = 0.0
            for word in self.CARNATIC_BOOST_WORDS:
                if word in query_lower and word in text_lower:
                    boost += 15.0  # Give a significant boost for matching specific classical terms
            
            hybrid_score = (0.6 * semantic_score) + (0.4 * overlap_score) + boost + chunk.get("score_modifier", 0.0)
            chunk["score"] = float(np.clip(hybrid_score, 1.0, 100.0))

# Singleton instance
reranker_instance = CarnaticReranker()

def rerank_chunks(query: str, chunks: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """Reranks chunks using the singleton CarnaticReranker."""
    return reranker_instance.rerank(query, chunks, top_n)
