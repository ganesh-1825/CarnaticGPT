import sys
import json
from pathlib import Path
sys.path.append('c:\\Users\\HP\\OneDrive\\Desktop\\CarnaticGPT')
from backend.services.faiss_store import FAISSStore
from backend.services.ingest import ingest_csv

def run():
    store = FAISSStore()
    
    # Remove all chunks from CarnaticSongsDatabase
    to_keep = []
    to_keep_meta = []
    
    deleted = 0
    for i, meta in enumerate(store.metadata):
        if meta.get("book_name") == "CarnaticSongsDatabase":
            deleted += 1
        else:
            to_keep.append(store.index.reconstruct(i))
            to_keep_meta.append(meta)
            
    print(f"Deleted {deleted} chunks from CarnaticSongsDatabase.")
    
    import faiss
    import numpy as np
    
    new_index = faiss.IndexFlatIP(store.index.d)
    if to_keep:
        new_index.add(np.array(to_keep, dtype=np.float32))
        
    store.index = new_index
    store.metadata = to_keep_meta
    # Rebuild known_hashes
    store.known_hashes = {m.get("id") for m in to_keep_meta if m.get("id")}
    store.save()
    print("Saved cleaned index.")
    
    csv_path = Path('c:/Users/HP/OneDrive/Desktop/CarnaticGPT/data/music_dataset/CarnaticSongsDatabase.csv')
    print("Re-ingesting CSV with new ingest.py code...")
    ingest_csv(csv_path)

if __name__ == '__main__':
    run()
