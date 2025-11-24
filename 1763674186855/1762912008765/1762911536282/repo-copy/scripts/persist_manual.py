import sqlite3, json, time, uuid, os, sys
sys.path.insert(0, os.path.abspath(os.getcwd()))
# Adjusted to match existing DB schema (no 'emotion' column)
p='data/memory.sqlite'
print('db exists', os.path.exists(p))
conn=sqlite3.connect(p)
cur=conn.cursor()
new_id=str(uuid.uuid4())
payload={'prompt':'entropy test','answer':'sample answer saved manually'}
# Insert into existing schema: id, ts, type, payload, trace_id, ttl_s, pinned
cur.execute("INSERT OR REPLACE INTO events(id, ts, type, payload, trace_id, ttl_s, pinned) VALUES (?,?,?,?,?,?,?)",
            (new_id, time.time(), 'agent_answer', json.dumps(payload, ensure_ascii=False), new_id, None, 0))
conn.commit()
print('inserted', new_id)
# verify count of agent_answer
cur.execute("SELECT count(*) FROM events WHERE type='agent_answer'")
print('count_agent_answer', cur.fetchone()[0])
conn.close()
# Now create a fresh bridge instance and import from this db
from Core_Memory.Conscious_Bridge import ConsciousBridge
nb=ConsciousBridge(stm_capacity=8)
loaded=nb.import_ltm_from_db(db_path=p)
print('loaded_into_bridge', loaded, 'nb_ltm_len', len(nb.ltm))
rows=nb.query(type='agent_answer', scope='ltm')
print('rows found via bridge', len(rows))
if rows:
    print('sample id', rows[-1]['id'])
