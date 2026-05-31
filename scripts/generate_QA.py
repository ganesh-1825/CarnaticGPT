import os
import sys
import json
import re
import requests
from utils import setup_logger

logger = setup_logger("QAGenerator")

def generate_qa_with_api(chunk_text, api_key, engine="gemini"):
    """Queries OpenAI or Gemini to generate high-fidelity Carnatic music QAs from a text chunk."""
    prompt = f"""
    Read the following text about South Indian Carnatic Music and generate 2 high-quality questions and detailed answers based strictly on this text.
    Format your response as a valid JSON array of objects, where each object has "question" and "answer" keys.
    Do not include markdown tags like ```json or anything else. Just the raw JSON array.
    
    Text:
    "{chunk_text}"
    """
    
    try:
        if engine == "gemini":
            url = f"https://generativetool.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                res_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                # Clean up any potential markdown wraps
                res_text = re.sub(r'```json\s*|\s*```', '', res_text).strip()
                return json.loads(res_text)
        elif engine == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                res_text = response.json()['choices'][0]['message']['content'].strip()
                res_text = re.sub(r'```json\s*|\s*```', '', res_text).strip()
                return json.loads(res_text)
    except Exception as e:
        logger.warning(f"API QA generation failed: {e}. Falling back to Rule-based generator.")
    return None

def generate_qa_rule_based(chunk_text, chunk_id):
    """Provides high-quality synthetic Carnatic QA pairs from text analysis."""
    qa_list = []
    
    # Simple semantic heuristics for Carnatic music
    if "mayamalavagowla" in chunk_text.lower():
        qa_list.append({
            "question": "What is the structure of Mayamalavagowla raga?",
            "answer": "Raga Mayamalavagowla is the 15th Melakarta raga in Carnatic music. It has a symmetrical structure with notes: Shadjam (S), Suddha Rishabham (R1), Antara Gandharam (G3), Suddha Madhyamam (M1), Panchamam (P), Suddha Dhaivatham (D1), and Kakali Nishadham (N3)."
        })
        qa_list.append({
            "question": "Why is Mayamalavagowla chosen for beginner lessons?",
            "answer": "Mayamalavagowla is chosen for beginner lessons because the intervals between successive notes (especially S to R1, and P to D1) are uniform semitones, making it easier for students to tune their ears to note transitions."
        })
    elif "dikshitar" in chunk_text.lower():
        qa_list.append({
            "question": "Who was Muthuswami Dikshitar and what is his legacy?",
            "answer": "Muthuswami Dikshitar (1775–1835) was a legendary South Indian composer, poet, and singer. He is part of the Trinity of Carnatic Music. His compositions are characterized by their rich Sanskrit lyrics, slow tempo (vilambita kala), and profound ragalakshana descriptions."
        })
        qa_list.append({
            "question": "What are some distinctive features of Dikshitar's compositions?",
            "answer": "Dikshitar's compositions are primarily in Sanskrit and feature a raga mudra (the name of the raga embedded in the lyrics). They often describe temples, architecture, and advanced concepts of yoga and mantra shastra."
        })
    elif "composers" in chunk_text.lower() or "tyagaraja" in chunk_text.lower():
        qa_list.append({
            "question": "Who comprise the Trinity of Carnatic Music?",
            "answer": "The Trinity of Carnatic Music comprises Saint Tyagaraja, Muthuswami Dikshitar, and Syama Sastry. They lived in the late 18th and early 19th centuries in Thanjavur and revolutionized Carnatic music with their compositional formats."
        })
    
    # Generic fallback based on text snippet
    if not qa_list:
        words = chunk_text.split()
        snippet = " ".join(words[:6]) + "..."
        qa_list.append({
            "question": f"What key concepts are discussed regarding {snippet}?",
            "answer": f"The text discusses classical Carnatic themes, specifically elaborating that: {chunk_text[:180]}..."
        })
        
    return qa_list

def run_qa_generation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chunks_file = os.path.join(base_dir, 'data', 'chunks', 'chunks.json')
    output_dir = os.path.join(base_dir, 'data', 'generated_QA')
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(chunks_file):
        logger.error(f"Chunks file not found at {chunks_file}. Please run chunk_text.py first.")
        return
        
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    # Read API keys from .env if active
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    engine = "gemini" if os.environ.get("GEMINI_API_KEY") else "openai"
    
    dataset = []
    logger.info(f"Generating QAs for {len(chunks)} chunks...")
    
    for i, chunk in enumerate(chunks[:20]): # Limit to first 20 chunks for safety/speed
        chunk_text = chunk["text"]
        chunk_id = chunk["chunk_id"]
        
        qa_pairs = None
        if api_key:
            qa_pairs = generate_qa_with_api(chunk_text, api_key, engine)
            
        if not qa_pairs:
            qa_pairs = generate_qa_rule_based(chunk_text, chunk_id)
            
        for pair in qa_pairs:
            pair["chunk_id"] = chunk_id
            pair["source_metadata"] = chunk["metadata"]
            dataset.append(pair)
            
        if (i+1) % 5 == 0:
            logger.info(f"Processed {i+1}/{len(chunks)} chunks.")
            
    # Save the dataset
    out_file = os.path.join(output_dir, "dataset_qa.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    # Also save to dataset folder
    music_dataset_file = os.path.join(base_dir, 'data', 'datasets', 'music_dataset.json')
    os.makedirs(os.path.dirname(music_dataset_file), exist_ok=True)
    with open(music_dataset_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Pipeline: QA generation complete. Generated {len(dataset)} QA pairs. Saved to {out_file} and {music_dataset_file}")

if __name__ == '__main__':
    run_qa_generation()
