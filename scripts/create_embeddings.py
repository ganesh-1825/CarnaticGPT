import os
import sys
import json
import numpy as np

# Ensure scripts folder is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from scripts.utils import setup_logger
except ImportError:
    from utils import setup_logger

logger = setup_logger("EmbeddingGenerator")

def get_embeddings_model(model_name="all-MiniLM-L6-v2"):
    """Loads SentenceTransformer model. Falls back to a simple mock embedder
    if sentence-transformers package is missing, or if 'mock' is explicitly requested.
    """
    if model_name == "mock":
        logger.info("Explicitly requested mock embedding model. Loading MockTransformer...")
        return MockTransformer()
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SentenceTransformer model: {model_name}")
        return SentenceTransformer(model_name)
    except ImportError:
        logger.warning("sentence-transformers package not installed. Using semantic bag-of-words tf-idf simulation.")
        return MockTransformer()

class MockTransformer:
    """Simulates a sentence embedder using standardized token indexing."""
    def __init__(self):
        self.dimension = 384
        
    def encode(self, texts, show_progress_bar=False, *args, **kwargs):
        # Generate simple but consistent pseudorandom vectors based on words present
        if isinstance(texts, str):
            texts = [texts]
            
        vectors = []
        for text in texts:
            words = text.lower().split()
            vec = np.zeros(self.dimension, dtype=np.float32)
            for w in words:
                # Deterministic seed from hash
                seed = sum(ord(c) for c in w) % self.dimension
                vec[seed] += 1.0
                
            # Add small noise for uniqueness
            np.random.seed(len(text))
            vec += np.random.normal(0, 0.05, self.dimension)
            
            # Normalize vector
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
            
        return np.array(vectors, dtype=np.float32)

def run_indexing():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chunks_file = os.path.join(base_dir, 'data', 'chunks', 'chunks.json')
    vector_db_dir = os.path.join(base_dir, 'vectorDB', 'faiss_index')
    metadata_dir = os.path.join(base_dir, 'vectorDB', 'metadata')
    
    os.makedirs(vector_db_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)
    
    if not os.path.exists(chunks_file):
        logger.error(f"Chunks file not found at {chunks_file}. Run chunk_text.py first!")
        return
        
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    if not chunks:
        logger.warning("No chunks found to embed.")
        return
        
    texts = [c["text"] for c in chunks]
    from dotenv import load_dotenv
    load_dotenv()
    model_name = os.environ.get("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    embedder = get_embeddings_model(model_name)
    
    logger.info(f"Generating embeddings for {len(texts)} text chunks...")
    embeddings = embedder.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype=np.float32)
    
    # Save the raw numpy embeddings for direct fallback loading
    embeddings_file = os.path.join(base_dir, 'data', 'embeddings', 'embeddings.npy')
    os.makedirs(os.path.dirname(embeddings_file), exist_ok=True)
    np.save(embeddings_file, embeddings)
    
    # Attempt FAISS build
    faiss_built = False
    try:
        import faiss
        logger.info("FAISS library detected. Constructing FAISS IndexFlatL2...")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        faiss_path = os.path.join(vector_db_dir, "index.faiss")
        faiss.write_index(index, faiss_path)
        logger.info(f"Saved FAISS index to {faiss_path}")
        faiss_built = True
    except ImportError:
        logger.warning("FAISS library not installed. Standardizing NumPy Vector database fallback.")
    except Exception as e:
        logger.error(f"FAISS construction failed: {e}")
        
    # Save index metadata (maps index numbers back to the exact text chunk details)
    metadata_file = os.path.join(metadata_dir, "metadata.json")
    metadata_records = []
    for i, c in enumerate(chunks):
        metadata_records.append({
            "index_id": i,
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "metadata": c["metadata"]
        })
        
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata_records, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Saved database indexing metadata mapping to {metadata_file}")
    logger.info(f"Pipeline: Indexing complete. Indexed {len(chunks)} chunks. FAISS: {faiss_built}")

if __name__ == '__main__':
    run_indexing()
