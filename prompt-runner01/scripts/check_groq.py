import os, requests, json
key = os.environ.get('GROQ_API_KEY')
print('GROQ_API_KEY present:', bool(key))
headers = {'Authorization': f'Bearer {key}'}
try:
    r = requests.get('https://api.groq.com/openai/v1/models', headers=headers, timeout=10)
    print('GET /models', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text[:1000])
except Exception as e:
    print('Models request error:', e)

print('\nTrying minimal chat completion...')
payload = {
    # pick a valid model: prefer groq/compound, groq/compound-mini, or llama-3.3-70b-versatile
    'model': 'groq/compound',
    'messages': [
        {'role':'system','content':'You are a JSON-only instruction generator.'},
        {'role':'user','content':'{"prompt":"test"}'}
    ],
    'temperature':0,
    'max_tokens':64
}
try:
    r2 = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=payload, timeout=10)
    print('POST /chat/completions', r2.status_code)
    try:
        print(json.dumps(r2.json(), indent=2)[:2000])
    except Exception:
        print(r2.text[:2000])
except Exception as e:
    print('Chat request error:', e)
