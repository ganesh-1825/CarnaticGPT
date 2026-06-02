"""
ingest.py
Carnatic GPT – Full ingestion pipeline.
Reads cleaned_chunks.json → generates embeddings → builds FAISS index.
Can be called standalone or imported by upload_pdf.py for incremental updates.
"""

import sys
import json
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer

# Reconfigure stdout to use UTF-8 on Windows console to avoid encoding crashes
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
CHUNKS_PATH = Path("data/chunks/cleaned_chunks.json")
INDEX_PATH   = Path("data/vectorDB/index.faiss")
META_PATH    = Path("data/vectorDB/metadata.json")
MODEL_NAME   = "all-MiniLM-L6-v2"
BATCH_SIZE   = 256


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def load_chunks(path: Path = CHUNKS_PATH) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def embed_chunks(
    chunks: List[Dict],
    model: SentenceTransformer,
    batch_size: int = BATCH_SIZE,
) -> np.ndarray:
    texts = [c["content"] for c in chunks]
    all_embeddings = []
    total = len(texts)
    for start in range(0, total, batch_size):
        batch = texts[start : start + batch_size]
        embeddings = model.encode(
            batch, convert_to_numpy=True,
            normalize_embeddings=True,   # L2-normalised → inner product == cosine
            show_progress_bar=False,
        )
        all_embeddings.append(embeddings)
        done = min(start + batch_size, total)
        print(f"  Embedded {done}/{total} chunks …", end="\r")
    print()
    return np.vstack(all_embeddings).astype("float32")


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """Build IndexFlatIP (inner product) on L2-normalised vectors = cosine similarity."""
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)   # inner product on unit vectors = cosine
    faiss.normalize_L2(embeddings)   # ensure normalised (belt-and-suspenders)
    index.add(embeddings)
    return index


def save_index(index: faiss.Index, chunks: List[Dict], embeddings: Optional[np.ndarray] = None):
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    # Also save raw numpy embeddings as fallback for retrieval.py
    if embeddings is not None:
        np.save(str(INDEX_PATH.parent / "embeddings.npy"), embeddings)
        print(f"  ✓ Saved embeddings → {INDEX_PATH.parent / 'embeddings.npy'}")
    print(f"  ✓ Saved index    → {INDEX_PATH}")
    print(f"  ✓ Saved metadata → {META_PATH}")


# ─────────────────────────────────────────────
# INCREMENTAL UPDATE (used by upload_pdf.py)
# ─────────────────────────────────────────────
def incremental_update(new_chunks: List[Dict], model: Optional[SentenceTransformer] = None):
    """
    Add new chunks to an existing FAISS index and metadata store.
    Creates from scratch if index doesn't exist yet.
    """
    if model is None:
        model = SentenceTransformer(MODEL_NAME)

    # Load existing metadata
    existing_chunks: List[Dict] = []
    if META_PATH.exists():
        with open(META_PATH, "r", encoding="utf-8") as f:
            existing_chunks = json.load(f)

    existing_ids = {c["id"] for c in existing_chunks}
    truly_new = [c for c in new_chunks if c["id"] not in existing_ids]

    if not truly_new:
        print("  No new unique chunks to add.")
        return

    print(f"  Adding {len(truly_new)} new chunks to index …")
    new_embeddings = embed_chunks(truly_new, model)

    if INDEX_PATH.exists():
        index = faiss.read_index(str(INDEX_PATH))
        index.add(new_embeddings)
    else:
        index = build_faiss_index(new_embeddings)

    all_chunks = existing_chunks + truly_new
    save_index(index, all_chunks)
    print(f"  ✓ Index now contains {index.ntotal} vectors from {len(all_chunks)} chunks")


# ─────────────────────────────────────────────
# MAIN FULL BUILD
# ─────────────────────────────────────────────
def main():
    print("\n=== CarnaticGPT Ingestion Pipeline ===\n")

    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned chunks not found at {CHUNKS_PATH}.\n"
            "Run:  python scripts/chunk_text.py  first."
        )

    print("Loading chunks …")
    chunks = load_chunks()
    print(f"  → {len(chunks):,} chunks loaded")

    # Stats by type
    by_type: Dict[str, int] = {}
    for c in chunks:
        by_type[c.get("type", "unknown")] = by_type.get(c.get("type", "unknown"), 0) + 1
    for t, n in sorted(by_type.items()):
        print(f"     {t:<20}: {n:,}")

    print(f"\nLoading embedding model: {MODEL_NAME} …")
    model = SentenceTransformer(MODEL_NAME)

    print(f"\nGenerating embeddings (batch={BATCH_SIZE}) …")
    embeddings = embed_chunks(chunks, model)
    print(f"  → Embedding matrix: {embeddings.shape}")

    print("\nBuilding FAISS index …")
    index = build_faiss_index(embeddings)
    print(f"  → Index size: {index.ntotal} vectors, dim={embeddings.shape[1]}")

    print("\nSaving …")
    save_index(index, chunks, embeddings)

    print("\n✓ Ingestion complete.")
    print(f"  Total vectors : {index.ntotal:,}")
    print(f"  Chunk metadata: {len(chunks):,}")


if __name__ == "__main__":
    main()