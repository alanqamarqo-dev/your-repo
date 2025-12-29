import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'sessions/web_bd43f167.json'
with open(p, 'rb') as f:
    b = f.read()
print('BYTES[:200]:', b[:200])
try:
    print('\nAS UTF-8:\n')
    print(b.decode('utf-8'))
except Exception as e:
    print('\nutf-8 decode failed:', e)
try:
    t = b.decode('latin-1')
    print('\nAS LATIN-1 (first 200 chars):\n')
    print(t[:200])
    try:
        rec = t.encode('latin-1').decode('utf-8')
        print('\nRECOVERED UTF-8 (first 200 chars):\n')
        print(rec[:200])
    except Exception as e2:
        print('\nrecover failed', e2)
except Exception as e3:
    print('\nlatin1 decode failed', e3)
