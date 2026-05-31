import re
from backend.logger import logger
from backend.raga_knowledge_base import find_raga_key, get_raga_info

def detect_query_type(query: str) -> str:
    """Classifies the user query into intent categories: comparison, person, explanation, quiz, or general."""
    query_lower = query.lower()
    
    if "compare" in query_lower or " vs " in query_lower or "versus" in query_lower:
        logger.info("Detected query type: comparison")
        return "comparison"
    elif "who" in query_lower or "biography" in query_lower or "composer" in query_lower:
        logger.info("Detected query type: person")
        return "person"
    elif "explain" in query_lower or "definition" in query_lower or "what is" in query_lower:
        logger.info("Detected query type: explanation")
        return "explanation"
    elif "quiz" in query_lower or "test" in query_lower or "question" in query_lower:
        logger.info("Detected query type: quiz")
        return "quiz"
    
    logger.info("Detected query type: general")
    return "general"

def extract_raga(query: str) -> str:
    """Extracts a single raga entity from the query using the comprehensive knowledge base."""
    raga_key = find_raga_key(query)
    if raga_key:
        info = get_raga_info(raga_key)
        if info:
            return info["name"]
    return None

def extract_ragas(query: str) -> dict:
    """Extracts raga entity names for comparison query structures (e.g. 'Compare RagaA vs RagaB')."""
    query_lower = query.lower()
    
    # 1. Try standard 'compare raga1 vs raga2' pattern
    pattern_vs = r'compare\s+(.*?)\s+vs\s+(.*)'
    match_vs = re.search(pattern_vs, query_lower)
    if match_vs:
        r1_raw = match_vs.group(1).replace("raga", "").strip()
        r2_raw = match_vs.group(2).replace("raga", "").strip()
        
        # Use find_raga_key to resolve aliases
        r1_key = find_raga_key(r1_raw)
        r2_key = find_raga_key(r2_raw)
        
        if r1_key and r2_key:
            return {"raga1": r1_key, "raga2": r2_key}
        
    # 2. Try 'compare raga1 and raga2' pattern
    pattern_and = r'compare\s+(.*?)\s+and\s+(.*)'
    match_and = re.search(pattern_and, query_lower)
    if match_and:
        r1_raw = match_and.group(1).replace("raga", "").strip()
        r2_raw = match_and.group(2).replace("raga", "").strip()
        
        r1_key = find_raga_key(r1_raw)
        r2_key = find_raga_key(r2_raw)
        
        if r1_key and r2_key:
            return {"raga1": r1_key, "raga2": r2_key}
        
    # 3. Fallback for just 'raga1 vs raga2'
    pattern_fallback = r'(.*?)\s+vs\s+(.*)'
    match_fallback = re.search(pattern_fallback, query_lower)
    if match_fallback:
        r1_raw = match_fallback.group(1).replace("raga", "").strip()
        r2_raw = match_fallback.group(2).replace("raga", "").strip()
        
        r1_key = find_raga_key(r1_raw)
        r2_key = find_raga_key(r2_raw)
        
        if r1_key and r2_key:
            return {"raga1": r1_key, "raga2": r2_key}
        
    return None
