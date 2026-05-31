import json
import os

with open("data/processed/music_data.json", encoding="utf-8") as f:
    songs = json.load(f)

chunks = []

for i, song in enumerate(songs):
    text = f"""Song: {song['song_name']}
Raga: {song['ragam']}
Composer: {song['composer']}
Janya Number: {song['janya_number']}
Youtube: {song['youtube']}"""

    chunks.append({
        "id": f"music_{i}",
        "content": text.strip(),
        "source": "CarnaticSongsDatabase.csv",
        "type": "music"
    })

with open("data/chunks/music_chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=4, ensure_ascii=False)

print(f"{len(chunks)} chunks created")
