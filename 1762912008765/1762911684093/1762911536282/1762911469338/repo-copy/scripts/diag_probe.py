import requests, json

SERVER = 'http://127.0.0.1:8000'
PROMPT = """(explanatory) تفصيل: المشكلة: صمّم نظام ري لحديقة صغيرة (10×20م) بميزانية 1000$، ثم اشرح كيف تطبّق نفس مبادئ التدفق على تنظيم حركة المرور في تقاطع مزدحم. اذكر القيود، المقايضات، وأدوات القياس. اختم بخطوات تنفيذ."""


def pretty(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


print('Posting to /process...')
try:
    r = requests.post(SERVER + '/process', json={'text': PROMPT}, timeout=120)
    print('Status:', r.status_code)
    try:
        print(pretty(r.json()))
    except Exception:
        print('Non-JSON response:', r.text)
except Exception as e:
    print('Process request failed:', e)

print('\nPosting to /rag/answer...')
try:
    r2 = requests.post(SERVER + '/rag/answer', json={'query': PROMPT}, timeout=120)
    print('Status:', r2.status_code)
    try:
        print(pretty(r2.json()))
    except Exception:
        print('Non-JSON response:', r2.text)
except Exception as e:
    print('RAG request failed:', e)

# Also try hitting /chat to see how the server logs incoming text
print('\nPosting to /chat...')
try:
    r3 = requests.post(SERVER + '/chat', json={'text': PROMPT}, timeout=120)
    print('Status:', r3.status_code)
    try:
        print(pretty(r3.json()))
    except Exception:
        print('Non-JSON response:', r3.text)
except Exception as e:
    print('Chat request failed:', e)
