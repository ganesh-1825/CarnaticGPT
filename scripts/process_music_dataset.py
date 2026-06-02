import pandas as pd
import json
import os

CSV_PATH = "data/music_dataset/CarnaticSongsDatabase.csv"

OUTPUT_PATH = "data/processed/ragas.json"

print("Loading Carnatic dataset...")

df = pd.read_csv(CSV_PATH)

print(f"Loaded {len(df)} rows")

ragas = []

for _, row in df.iterrows():

    ragas.append({

        "song": str(row.get("Song Name", "")),

        "raga": str(row.get("Ragam", "")),

        "composer": str(row.get("Composer", "")),

        "youtube": str(row.get("Youtube Link", ""))

    })

os.makedirs(
    "data/processed",
    exist_ok=True
)

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        ragas,
        f,
        indent=2,
        ensure_ascii=False
    )

print(f"Saved {len(ragas)} ragas")
