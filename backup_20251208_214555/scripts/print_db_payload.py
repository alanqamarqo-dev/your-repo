import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'medical_seed.sqlite')
DB_PATH = os.path.normpath(DB_PATH)

if not os.path.exists(DB_PATH):
    print(f"DB not found: {DB_PATH}")
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT payload FROM events LIMIT 1")
r = cur.fetchone()
conn.close()

if not r or not r[0]:
    print("No payload found in DB")
    raise SystemExit(1)

payload = r[0]
# try to parse as JSON
try:
    data = json.loads(payload)
    # common key 'text' used when ingesting
    text = data.get('text') if isinstance(data, dict) else None
    if not text:
        # fallback: pretty-print whole object
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(text)
except Exception:
    # not JSON, print raw
    print(payload)
