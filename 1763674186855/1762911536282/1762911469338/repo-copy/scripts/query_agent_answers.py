import sqlite3
conn=sqlite3.connect('data/memory.sqlite')
cur=conn.cursor()
cur.execute("SELECT id, ts, type, payload FROM events WHERE type='agent_answer' ORDER BY ts DESC LIMIT 5")
rows=cur.fetchall()
print('found', len(rows))
for r in rows:
    print(r[0], r[2], r[3][:200])
conn.close()
