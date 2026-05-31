import re
from typing import List, Dict, Any
from backend.logger import logger

class CarnaticReranker:
    """Reranks retrieved text chunks based on semantic similarity, exact term matches,
    and domain-specific keywords for Carnatic music.
    """
    
    # Domain-specific words that merit high relevance boosts if matched in both query and chunk
    CARNATIC_BOOST_WORDS = [
        "bhairavi", "kalyani", "mohanam", "mayamalavagowla", "mayamalavagaula",
        "tyagaraja", "dikshitar", "sastry", "syama", "purandara",
        "tala", "raga", "swara", "gamaka", "sarali", "jantai", "alankaram",
        "mridangam", "veena", "violin", "flute", "sruthi", "melakarta",
        "prahalada", "vijayam", "sanskrit", "telugu", "lakshana"
    ]

    def __init__(self):
        logger.info("CarnaticReranker initialized.")

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        """Reranks a list of retrieved chunks using a hybrid scoring algorithm and returns top_n."""
        if not chunks:
            return []
            
        logger.info(f"Reranking {len(chunks)} chunks for query: '{query}'")
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        reranked_chunks = []
        for chunk in chunks:
            text_lower = chunk["text"].lower()
            text_words = set(re.findall(r'\w+', text_lower))
            
            # 1. Base semantic score from vector similarity
            semantic_score = chunk.get("score", 0.5)
            
            # 2. Keyword overlap score (Jaccard-like ratio)
            intersection = query_words.intersection(text_words)
            overlap_score = len(intersection) / len(query_words) if query_words else 0.0
            
            # 3. Domain boost (specialized Carnatic terms)
            boost = 0.0
            matched_boost_words = []
            for word in self.CARNATIC_BOOST_WORDS:
                if word in query_lower and word in text_lower:
                    boost += 0.15 # Give a significant boost for matching specific classical terms
                    matched_boost_words.append(word)
            
            # 4. Synthesizing hybrid score
            # We weight semantic score higher, but boost it based on keyword overlap and classical term matches
            hybrid_score = (0.6 * semantic_score) + (0.4 * overlap_score) + boost
            
            # Cap the final score at 0.99 for aesthetics and consistency
            final_score = min(0.99, max(0.01, hybrid_score))
            
            # Create a copy of the chunk with updated score and audit metadata
            new_chunk = dict(chunk)
            new_chunk["score"] = final_score
            new_chunk["original_semantic_score"] = semantic_score
            new_chunk["rerank_boost_applied"] = len(matched_boost_words) > 0
            
            reranked_chunks.append(new_chunk)
            
        # Sort chunks by the new hybrid score in descending order
        reranked_chunks.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"Top 3 reranked scores: {[round(c['score'], 3) for c in reranked_chunks[:top_n]]}")
        return reranked_chunks[:top_n]

# Singleton instance for easy reuse
reranker_instance = CarnaticReranker()

def rerank_chunks(query: str, chunks: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
    """Convenience helper to rerank chunks using the singleton CarnaticReranker."""
    return reranker_instance.rerank(query, chunks, top_n)
