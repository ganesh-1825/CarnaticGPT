import requests, time

time.sleep(25)
url = 'http://localhost:8000/api/chat/query'
queries = [
    'Recommend Bhairavi recordings in 5 Kattai. Show recordings in 2 Kattai.',
    'Why is Sankarabharanam considered fundamental?',
    'What are the characteristic prayogas of Kambhoji?',
    'Which ragas are suitable for elaborate alapana?',
    'How are gamakas used in Bhairavi?',
    'Compare Bhairavi and Manji',
]
for q in queries:
    print(f'\n===== {q} =====')
    try:
        res = requests.post(url, json={'query': q}, timeout=30)
        data = res.json()
        print(data.get('answer', 'NO ANSWER'))
        route = data.get('route', '?')
        print(f'[route: {route}]')
    except Exception as e:
        print(f'ERROR: {e}')
