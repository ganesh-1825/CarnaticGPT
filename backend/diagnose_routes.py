"""
Diagnostic script: Tests query routing and full pipeline answer.
Run from project root: python backend/diagnose_routes.py
"""
import logging
logging.disable(logging.WARNING)

from backend.services.query_router import route_query
from backend.services.retrieval import answer_question

TESTS = [
    "What is RTP?",
    "Write the arohana and avarohana of Kalyani",
    "What are the Pancharatna Kritis?",
    "Who composed Balagopala?",
    "Explain Kalyani raga",
    "What is Niraval?",
]

print("=" * 70)
print("STEP 1 — ROUTE DETECTION")
print("=" * 70)
for q in TESTS:
    r = route_query(q)
    print(f"  Q : {q}")
    print(f"  -> mode={r.mode}  intent={r.intent}  raga={r.raga_name}")
    print()

print("=" * 70)
print("STEP 2 — FULL PIPELINE ANSWERS")
print("=" * 70)
for q in TESTS:
    res = answer_question(q)
    route  = res.get("route", "?")
    method = res.get("synthesis_method", "?")
    answer = res.get("answer", "")[:250].replace("\n", " ")
    print(f"  Q      : {q}")
    print(f"  route  : {route}")
    print(f"  method : {method}")
    print(f"  answer : {answer}")
    print()
