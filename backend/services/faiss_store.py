"""
faiss_store.py
--------------
Singleton FAISS store. Handles:
  - Loading / saving index + metadata to disk
  - Appending new documents (with duplicate detection)
  - Typed similarity search (filter by chunk type)
  - Cosine similarity scores normalised to 0-100
"""

import os
import pickle
import logging
import threading
import json
import hashlib
from pathlib import Path

import faiss
import numpy as np

logger = logging.getLogger(__name__)

INDEX_DIR = Path(os.getenv("FAISS_INDEX_DIR", "data/vectorDB"))
INDEX_FILE = INDEX_DIR / "index.faiss"
META_FILE = INDEX_DIR / "metadata.pkl"
META_JSON = INDEX_DIR / "metadata.json"
HASHES_FILE = INDEX_DIR / "hashes.pkl"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DIMENSION = 384


class BM25Searcher:
    def __init__(self, corpus: list[dict]):
        import re
        import math
        from collections import Counter, defaultdict
        
        self.corpus = corpus
        self.doc_len = []
        self.vocab_df = Counter()
        self.inverted_index = defaultdict(list)
        
        for idx, doc in enumerate(corpus):
            text = (doc.get("content") or doc.get("text") or "").lower()
            words = re.findall(r"\b[a-z]{3,}\b", text)
            self.doc_len.append(len(words))
            word_counts = Counter(words)
            for word, freq in word_counts.items():
                self.inverted_index[word].append((idx, freq))
                self.vocab_df[word] += 1
                
        self.n_docs = len(corpus)
        self.avg_doc_len = sum(self.doc_len) / self.n_docs if self.n_docs > 0 else 1.0
        
        # Precompute IDFs
        self.idfs = {}
        for word, df in self.vocab_df.items():
            self.idfs[word] = math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1.0)
            
    def search(self, query: str, top_k: int = 150) -> list[tuple[int, float]]:
        import re
        from collections import defaultdict
        
        query_words = re.findall(r"\b[a-z]{3,}\b", query.lower())
        if not query_words:
            return []
            
        scores = defaultdict(float)
        k1 = 1.5
        b = 0.75
        
        for word in query_words:
            idf = self.idfs.get(word, 0)
            if idf <= 0:
                continue
            postings = self.inverted_index.get(word, [])
            for doc_idx, freq in postings:
                d_len = self.doc_len[doc_idx]
                tf_denom = freq + k1 * (1.0 - b + b * (d_len / self.avg_doc_len))
                scores[doc_idx] += idf * (freq * (k1 + 1.0)) / tf_denom
                
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_k]


class FAISSStore:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._initialised = False
                    cls._instance = inst
        return cls._instance

    def __init__(self):
        if self._initialised:
            return
        self._initialised = True
        self._write_lock = threading.Lock()

        logger.info("Loading embedding model via get_cached_embedder...")
        from backend.model_loader import get_cached_embedder
        self.model = get_cached_embedder()

        self.metadata: list[dict] = []
        self.known_hashes: set[str] = set()
        self.bm25 = None

        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self):
        if INDEX_FILE.exists() and (META_FILE.exists() or META_JSON.exists()):
            try:
                self.index = faiss.read_index(str(INDEX_FILE))

                if META_FILE.exists():
                    with open(META_FILE, "rb") as f:
                        self.metadata = pickle.load(f)
                elif META_JSON.exists():
                    with open(META_JSON, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                        # Ensure each metadata entry has an 'id' for hashing if it's missing
                        for m in self.metadata:
                            if "id" not in m and "content" in m:
                                m["id"] = hashlib.sha256(m["content"].strip().lower().encode()).hexdigest()[:16]

                if HASHES_FILE.exists():
                    with open(HASHES_FILE, "rb") as f:
                        self.known_hashes = pickle.load(f)
                else:
                    # Rebuild hashes from metadata
                    self.known_hashes = {m.get("id", "") for m in self.metadata if m.get("id")}

                logger.info(
                    "Loaded FAISS index: %d vectors, %d metadata entries",
                    self.index.ntotal, len(self.metadata),
                )
            except Exception as e:
                logger.warning("Failed to load existing index (%s). Creating new.", e)
                self._create_new_index()
        else:
            # Check if old index exists and migrate it!
            old_faiss_dir = Path("vectorDB/faiss_index")
            if (old_faiss_dir / "index.faiss").exists() and (old_faiss_dir / "index.pkl").exists():
                logger.info("New FAISS index not found, but old vectorDB index exists. Migrating old index...")
                try:
                    self._migrate_old_index(old_faiss_dir)
                except Exception as e:
                    logger.error("Migration failed: %s. Creating new index.", e)
                    self._create_new_index()
            else:
                self._create_new_index()

    def _migrate_old_index(self, old_dir: Path):
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        logger.info("Loading old FAISS index via LangChain for migration...")
        embeddings_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        db = FAISS.load_local(str(old_dir), embeddings_model, allow_dangerous_deserialization=True)
        
        logger.info("Extracting %d documents from old FAISS store...", len(db.docstore._dict))
        
        self.index = faiss.IndexFlatIP(DIMENSION)
        self.metadata = []
        self.known_hashes = set()
        
        chunks_to_add = []
        for doc_id, doc in db.docstore._dict.items():
            text = doc.page_content
            meta = doc.metadata
            
            # Create a clean metadata structure matching the new format
            import hashlib
            h = hashlib.sha256(text.strip().lower().encode()).hexdigest()[:16]
            
            chunk = {
                "id": h,
                "content": text,
                "source": meta.get("source", "unknown"),
                "book_name": meta.get("book_name", "unknown"),
                "page_number": meta.get("page", 1),
                "type": meta.get("type", "theory"),
                "category": meta.get("type", "theory"),
                "chunk_index": 0,
                "char_count": len(text),
            }
            chunks_to_add.append(chunk)
            
        logger.info("Adding %d migrated documents to new FAISS index...", len(chunks_to_add))
        self.add_documents(chunks_to_add)
        logger.info("Migration successful! Saved %d documents to new FAISSStore.", len(chunks_to_add))

    def _create_new_index(self):
        self.index = faiss.IndexFlatIP(DIMENSION)
        self.metadata = []
        self.known_hashes = set()
        logger.info("Created new FAISS IndexFlatIP (dim=%d)", DIMENSION)

    def save(self):
        with self._write_lock:
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(INDEX_FILE))
            with open(META_FILE, "wb") as f:
                pickle.dump(self.metadata, f)
            with open(HASHES_FILE, "wb") as f:
                pickle.dump(self.known_hashes, f)
        logger.info("FAISS index saved (%d vectors)", self.index.ntotal)

    # ------------------------------------------------------------------
    # Add documents
    # ------------------------------------------------------------------

    def add_documents(self, chunks: list[dict]) -> int:
        """
        Embed and add chunks to the index.
        Skips chunks whose id hash is already present (dedup).
        Returns number of newly added chunks.
        """
        new_chunks = [c for c in chunks if c.get("id") not in self.known_hashes]
        if not new_chunks:
            logger.info("No new chunks to add (all duplicates).")
            return 0

        texts = [c["content"] for c in new_chunks]
        logger.info("Generating embeddings for %d new chunks...", len(texts))

        embeddings = self.model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True,   # L2 norm for cosine via IndexFlatIP
            convert_to_numpy=True,
        ).astype(np.float32)

        with self._write_lock:
            self.index.add(embeddings)
            for chunk in new_chunks:
                self.metadata.append(chunk)
                self.known_hashes.add(chunk["id"])

        self.save()
        logger.info("Added %d chunks. Total in index: %d", len(new_chunks), self.index.ntotal)
        return len(new_chunks)

    # ------------------------------------------------------------------
    # Similarity search
    # ------------------------------------------------------------------

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        type_filter: list[str] | None = None,
        min_score: float = 25.0,
    ) -> list[dict]:
        """
        Search FAISS + BM25 hybrid for the most relevant chunks.
        """
        if self.index.ntotal == 0:
            return []

        # Lazily build BM25 searcher
        if self.bm25 is None or len(self.bm25.corpus) != len(self.metadata):
            self.bm25 = BM25Searcher(self.metadata)

        # 1. Fetch Candidates from FAISS (Vector Search)
        # Fetch slightly more candidates to do meaningful re-ranking
        fetch_k = min(150, self.index.ntotal)
        q_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype(np.float32)

        distances, indices = self.index.search(q_emb, fetch_k)

        # Map FAISS results to normalized scores (0-100)
        vector_scores = {}
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            score = float(np.clip((dist + 1.0) / 2.0 * 100.0, 0.0, 100.0))
            vector_scores[idx] = score

        # 2. Fetch Candidates from BM25 Search
        bm25_results = self.bm25.search(query, top_k=150)
        max_bm25_score = bm25_results[0][1] if bm25_results else 0.0

        bm25_scores = {}
        for idx, score in bm25_results:
            # Normalize to 0-100 scale based on maximum score in current query
            norm_score = (score / max_bm25_score * 100.0) if max_bm25_score > 0 else 0.0
            bm25_scores[idx] = norm_score

        # 3. Combine Scores (Union of both)
        all_candidate_indices = set(vector_scores.keys()) | set(bm25_scores.keys())
        results = []

        for idx in all_candidate_indices:
            meta = self.metadata[idx]

            # Apply type filter
            if type_filter and meta.get("type") not in type_filter:
                continue

            v_score = vector_scores.get(idx, 20.0) # default fallback if only in BM25
            b_score = bm25_scores.get(idx, 0.0)

            # Hybrid score computation (50/50 balance)
            hybrid_score = 0.5 * v_score + 0.5 * b_score

            if hybrid_score < min_score:
                continue

            results.append({
                "text": meta.get("content", ""),
                "metadata": meta,
                "score": round(hybrid_score, 1),
            })

        # Sort by hybrid score descending and take top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        type_counts: dict[str, int] = {}
        books: set[str] = set()
        for m in self.metadata:
            t = m.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
            books.add(m.get("book_name", ""))
        return {
            "total_vectors": self.index.ntotal,
            "total_chunks": len(self.metadata),
            "indexed_books": len(books),
            "by_type": type_counts,
        }

    def is_book_indexed(self, book_name: str) -> bool:
        return any(m.get("book_name") == book_name for m in self.metadata)
