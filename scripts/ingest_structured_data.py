import os
import sys
import json
import numpy as np

# Ensure project root is visible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.logger import logger
from backend.model_loader import get_cached_embedder

def ingest_hindolam():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Path setup
    dataset_file = os.path.join(base_dir, 'data', 'datasets', 'hindolam_dataset.json')
    metadata_file = os.path.join(base_dir, 'vectorDB', 'metadata', 'metadata.json')
    embeddings_file = os.path.join(base_dir, 'data', 'embeddings', 'embeddings.npy')
    faiss_path = os.path.join(base_dir, 'vectorDB', 'faiss_index', 'index.faiss')
    
    if not os.path.exists(dataset_file):
        logger.error(f"Structured dataset file not found at: {dataset_file}")
        return
        
    logger.info("Loading structured Hindolam dataset...")
    with open(dataset_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Formulate a dense semantic text representation of the structured metadata
    compositions_text = ", ".join([f"'{c['name']}' ({c['talam']} Tala, by {c['composer']})" for c in data['compositions']])
    features_text = "; ".join(data['special_features'])
    samvadi_text = ", ".join(data['samvadi_swaras'])
    swaras_text = ", ".join(data['swarasthanas'])
    rasas_text = ", ".join(data['rasas'])
    
    semantic_chunk = (
        f"Raga Hindolam is a prominent South Indian classical Carnatic music raga. "
        f"Classified as an Audava Raga (a pentatonic scale employing five notes in both ascending and descending configurations), "
        f"it is a Janya raga derived from the 8th Melakarta parent, Hanuma Todi. "
        f"Its Hindustani music equivalent scale is Raga Malkouns. "
        f"The Swarasthanas (notes) employed are: {swaras_text}. "
        f"Scale: Arohana (ascending) is S G2 M1 D1 N2 S (represented as {data['arohana']}), "
        f"and Avarohana (descending) is S N2 D1 M1 G2 S (represented as {data['avarohana']}). "
        f"It evokes intense {rasas_text} rasas (compassion, devotion, and tranquility). "
        f"Special characteristics include: {features_text}. "
        f"Samvadi swara pairs are: {samvadi_text}. "
        f"Core signature compositions are: {compositions_text}."
    )
    
    logger.info("Formulated semantic chunk from structured JSON successfully.")
    
    # Create chunk record
    chunk_record = {
        "chunk_id": "raga_lakshana_p8_c1",
        "text": semantic_chunk,
        "metadata": {
            "source": "Ragas/Raga_Lakshana.txt",
            "category": "Ragas",
            "book_name": "Raga Lakshana",
            "page": 8,
            "word_count": len(semantic_chunk.split())
        }
    }
    
    # Embed the chunk using pre-warmed cached SentenceTransformer
    logger.info("Generating embedding vector...")
    embedder = get_cached_embedder()
    embedding_vector = embedder.encode([semantic_chunk], show_progress_bar=False)[0]
    embedding_vector = np.array(embedding_vector, dtype=np.float32)
    
    # Load and update metadata
    all_metadata = []
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                all_metadata = json.load(f)
        except Exception:
            pass
            
    # Check if hindolam chunk is already present to prevent duplicating it
    exists = False
    for idx, c in enumerate(all_metadata):
        if c.get("chunk_id") == "raga_lakshana_p8_c1":
            all_metadata[idx] = chunk_record
            exists = True
            target_idx = idx
            break
            
    if not exists:
        chunk_record["index_id"] = len(all_metadata)
        all_metadata.append(chunk_record)
        target_idx = len(all_metadata) - 1
        
    # Load and update embeddings array
    all_embeddings = None
    if os.path.exists(embeddings_file):
        try:
            all_embeddings = np.load(embeddings_file)
        except Exception:
            pass
            
    if all_embeddings is not None and all_embeddings.shape[0] > 0:
        if exists:
            # Replace existing embedding at the same index
            all_embeddings[target_idx] = embedding_vector
        else:
            # Append new embedding
            all_embeddings = np.vstack([all_embeddings, embedding_vector])
    else:
        all_embeddings = np.array([embedding_vector], dtype=np.float32)
        
    # Save back files
    os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
    os.makedirs(os.path.dirname(embeddings_file), exist_ok=True)
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)
        
    np.save(embeddings_file, all_embeddings)
    logger.info("Successfully updated metadata.json and embeddings.npy indices!")
    
    # Re-build FAISS flat index
    try:
        import faiss
        dimension = all_embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(all_embeddings)
        os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
        faiss.write_index(index, faiss_path)
        logger.info(f"Successfully rebuilt FAISS database index at {faiss_path}")
    except Exception as fe:
        logger.error(f"FAISS flat index rebuild skipped/failed: {fe}")
        
    print("\n=== Structured Ingestion Completed Successfully! ===")
    print(f"Raga: {data['raga']}")
    print(f"Ingested Semantic Chunk: '{semantic_chunk[:100]}...'")
    print("==================================================\n")

if __name__ == "__main__":
    ingest_hindolam()
