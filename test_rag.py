import sys
sys.path.append('c:\\Users\\HP\\OneDrive\\Desktop\\CarnaticGPT')
from backend.services.synthesizer import synthesize
from backend.services.faiss_store import FAISSStore

store = FAISSStore()
query = 'Play Bhairavi alapana'
chunks = store.similarity_search(query)
ans, method = synthesize(query, chunks)
print('Answer:\n', ans)

print('\n---\n')
query2 = 'What is the shruti of Maragatha-Manimaya?'
chunks2 = store.similarity_search(query2)
ans2, method2 = synthesize(query2, chunks2)
print('Answer2:\n', ans2)
