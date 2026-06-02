import sys
import json
from pathlib import Path
sys.path.append('c:\\Users\\HP\\OneDrive\\Desktop\\CarnaticGPT')
from backend.services.faiss_store import FAISSStore

store = FAISSStore()
music_chunks = [m for m in store.metadata if m.get("type") == "music"]
print(f"Total music chunks: {len(music_chunks)}")
if music_chunks:
    print("Sample music chunk:")
    for k, v in list(music_chunks[0].items())[:10]:
        print(f"  {k}: {v}")
    
    print("\nDo all music chunks have a song?")
    songs = [m.get("song") for m in music_chunks if m.get("song")]
    print(f"Total with song: {len(songs)}")
