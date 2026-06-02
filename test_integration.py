import sys
import os

# Set encoding to handle emojis in print statements
sys.stdout.reconfigure(encoding='utf-8')

# Add the project root to sys.path so backend module can be found
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.rag import execute_rag_pipeline

queries = [
    # Step 10 tests
    "Which songs belong to Aarabhi?",
    "Who composed Nagumomu?",
    "List songs by Tyagaraja.",
    "Which ragas belong to Janya number 22?",
    "Show songs in Abheri.",
    # Step 11 tests
    "Explain Hindolam and list songs in Hindolam.",
    "Compare Kalyani and Mohanam and give compositions.",
    "Who composed songs in Bhairavi?"
]

print("Starting Integration Tests...\n")

for q in queries:
    print(f"=====================================")
    print(f"QUERY: {q}")
    print(f"=====================================")
    
    try:
        response = execute_rag_pipeline(q)
        print(f"RESPONSE:\n{response['response']}\n")
        print(f"CONFIDENCE: {response['confidence']}")
        print(f"DETECTED RAGA: {response['detected_raga']}")
        if response.get("citations"):
            print(f"TOP SOURCE: {response['citations'][0]['book_name']} (Score: {response['citations'][0]['score']:.4f})")
    except Exception as e:
        print(f"ERROR: {e}")
        
    print("\n")
