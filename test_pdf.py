import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.rag import execute_rag_pipeline

queries = [
    "What does the paper say about Carnatic datasets?",
    "Explain computational musicology.",
    "Explain scalable extraction of Ragam metadata.",
    "How are Shruti and Talam used?",
    "Summarize the uploaded paper."
]

print("Starting PDF Extraction Tests...\n")

for q in queries:
    print(f"=====================================")
    print(f"QUERY: {q}")
    print(f"=====================================")
    try:
        response = execute_rag_pipeline(q)
        print(f"RESPONSE:\n{response['response']}\n")
        print(f"CONFIDENCE: {response['confidence']}")
        if response.get("citations"):
            print(f"TOP SOURCE: {response['citations'][0]['source']} (Score: {response['citations'][0]['score']:.4f})")
    except Exception as e:
        print(f"ERROR: {e}")
    print("\n")
