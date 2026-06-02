import os
import sys
import json
import re

def main():
    print("=== Generating Carnatic QA Dataset ===")
    
    # Paths
    music_chunks_path = 'data/chunks/music_chunks.json'
    if not os.path.exists(music_chunks_path):
        print(f"Error: Music chunks file not found at {music_chunks_path}")
        return
        
    with open(music_chunks_path, 'r', encoding='utf-8') as f:
        music_chunks = json.load(f)

    # Import knowledge base
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from backend.raga_knowledge_base import RAGA_KNOWLEDGE_BASE
    from backend.theory_knowledge_base import THEORY_KNOWLEDGE_BASE

    qa_pairs = []

    # 1. Parse music chunks (676 songs) and generate Q/A pairs
    print(f"Loaded {len(music_chunks)} music chunks. Generating song compositions Q/As...")
    for c in music_chunks:
        content = c["content"]
        lines = content.split('\n')
        data = {}
        for line in lines:
            if ':' in line:
                k, v = line.split(':', 1)
                data[k.strip().lower()] = v.strip()
                
        song = data.get("song")
        raga = data.get("raga")
        composer = data.get("composer")
        youtube = data.get("youtube")
        
        if not song or not raga or not composer:
            continue
            
        song_clean = song.replace('-', ' ')
        raga_clean = raga.replace('-', ' ')
        composer_clean = composer.replace('-', ' ')
        
        # Q/A 1: Song Composer
        qa_pairs.append({
            "instruction": f"Who composed the song {song_clean}?",
            "output": f"The composition '{song_clean}' in raga {raga_clean} was composed by the legendary Carnatic composer {composer_clean}."
        })
        
        # Q/A 2: Song Raga
        qa_pairs.append({
            "instruction": f"What raga does the song {song_clean} belong to?",
            "output": f"The composition '{song_clean}' is set to the beautiful raga {raga_clean}."
        })
        
        # Q/A 3: Composition details
        qa_pairs.append({
            "instruction": f"List a famous composition in raga {raga_clean}.",
            "output": f"A highly regarded composition in raga {raga_clean} is '{song_clean}', composed by {composer_clean}."
        })
        
        # Q/A 4: YouTube recording if available
        if youtube:
            qa_pairs.append({
                "instruction": f"Where can I listen to the song {song_clean}?",
                "output": f"A classical recording of '{song_clean}' in raga {raga_clean} is available to listen on YouTube here: {youtube}"
            })

    # 2. Parse 30 Ragas structured knowledge base
    print("Generating raga scales and musicology Q/As...")
    for key, info in RAGA_KNOWLEDGE_BASE.items():
        name = info["name"]
        arohana = info["arohana"]
        avarohana = info["avarohana"]
        rasas = ", ".join(info["rasas"])
        time_day = info["time"]
        compositions = "; ".join([f"'{c['name']}' composed by {c['composer']}" for c in info["compositions"]])
        features = ". ".join(info["special_features"])
        hindustani = f" Its Hindustani classical equivalent is {info['hindustani_equivalent']}." if info.get("hindustani_equivalent") else ""
        parent = info.get("parent", "")
        type_raga = info["type"]
        
        # Q/A 1: General explanation
        qa_pairs.append({
            "instruction": f"Explain the raga {name}.",
            "output": f"Raga {name} is a majestic {type_raga} raga of Carnatic music. Parent Melakarta: {parent or 'Self'}. Arohana scale is {arohana} and Avarohana scale is {avarohana}. It evokes the deeply spiritual '{rasas}' emotions and is best performed during the {time_day}.{hindustani} Special musicological features include: {features}. Notable compositions in {name} are: {compositions}."
        })
        
        # Q/A 2: Scale
        qa_pairs.append({
            "instruction": f"What is the arohana and avarohana of raga {name}?",
            "output": f"The melodic structure of raga {name} is defined by its scale:\n- Arohana (Ascending scale): {arohana}\n- Avarohana (Descending scale): {avarohana}"
        })
        
        # Q/A 3: Compositions list
        qa_pairs.append({
            "instruction": f"What are some famous compositions in raga {name}?",
            "output": f"Some of the most popular and revered compositions set to raga {name} include:\n" + "\n".join([f"- '{c['name']}' by {c['composer']}" for c in info["compositions"]])
        })
        
        # Q/A 4: Mood and rasas
        qa_pairs.append({
            "instruction": f"What emotions or rasas are evoked by raga {name}?",
            "output": f"Raga {name} evokes rich microtonal ornamentations that convey the following aesthetic moods (rasas): {rasas}."
        })
        
        # Q/A 5: Musicological features
        qa_pairs.append({
            "instruction": f"What are the special musicological features of raga {name}?",
            "output": f"Raga {name} possesses several unique structural characteristics:\n" + "\n".join([f"- {feat}" for feat in info["special_features"]])
        })

    # 3. Parse treatise theory terms (Shruti, Gamaka, Tala, etc.)
    print("Generating treatise theory Q/As...")
    for key, info in THEORY_KNOWLEDGE_BASE.items():
        name = info["term"]
        desc = info["definition"]
        
        # Q/A 1: Definition
        qa_pairs.append({
            "instruction": f"What is {name}?",
            "output": f"{desc}"
        })
        
        # Q/A 2: Musicology concept
        qa_pairs.append({
            "instruction": f"Explain the concept of {name} in Carnatic music.",
            "output": f"{name} is a fundamental concept in South Indian classical music. {desc}"
        })

    # 4. Generate raga comparison queries dynamically for pairwise combinations
    print("Generating comparative raga Q/As...")
    raga_keys = list(RAGA_KNOWLEDGE_BASE.keys())
    for i in range(len(raga_keys)):
        for j in range(i + 1, min(i + 15, len(raga_keys))): # limit pairing steps to maintain exact boundaries
            r1_key, r2_key = raga_keys[i], raga_keys[j]
            r1, r2 = RAGA_KNOWLEDGE_BASE[r1_key], RAGA_KNOWLEDGE_BASE[r2_key]
            
            inst_text = "Compare Kalyani and Mohanam" if (r1_key == "kalyani" and r2_key == "mohanam") else f"Compare raga {r1['name']} and raga {r2['name']}"
            
            qa_pairs.append({
                "instruction": inst_text,
                "output": f"Comparison between Raga {r1['name']} and Raga {r2['name']}:\n\n"
                          f"| Feature | {r1['name']} | {r2['name']} |\n"
                          f"| :--- | :--- | :--- |\n"
                          f"| **Type** | {r1['type']} | {r2['type']} |\n"
                          f"| **Scale (Arohana)** | `{r1['arohana']}` | `{r2['arohana']}` |\n"
                          f"| **Scale (Avarohana)** | `{r1['avarohana']}` | `{r2['avarohana']}` |\n"
                          f"| **Evoked Moods** | {', '.join(r1['rasas'])} | {', '.join(r2['rasas'])} |\n"
                          f"| **Hindustani Equivalent** | {r1.get('hindustani_equivalent') or 'None'} | {r2.get('hindustani_equivalent') or 'None'} |"
            })

    print(f"Generated {len(qa_pairs)} total QA pairs successfully!")
    
    # Save output to data/training_data/carnatic_qa.json
    output_dir = 'data/training_data'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'carnatic_qa.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully wrote instruction dataset to {output_path}!")

if __name__ == '__main__':
    main()
