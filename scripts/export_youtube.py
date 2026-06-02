import pandas as pd
import json
import os

df = pd.read_csv("c:/Users/HP/OneDrive/Desktop/CarnaticGPT/data/music_dataset/CarnaticSongsDatabase.csv")

records = []
for _, row in df.iterrows():
    if pd.notna(row["Youtube Link"]) and str(row["Youtube Link"]).strip():
        records.append({
            "song_name": str(row["Song Name"]),
            "ragam": str(row["Ragam"]).strip(),
            "composer": str(row["Composer"]),
            "youtube": str(row["Youtube Link"])
        })

output_path = "c:/Users/HP/OneDrive/Desktop/CarnaticGPT/frontend/src/data/youtube_ragas.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=4, ensure_ascii=False)

print(f"Exported {len(records)} youtube links to frontend.")
