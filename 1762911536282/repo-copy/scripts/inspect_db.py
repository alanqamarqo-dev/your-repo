import sqlite3
conn=sqlite3.connect('data/memory.sqlite')
cur=conn.cursor()
cur.execute("PRAGMA table_info(events);")
cols=cur.fetchall()
print('columns:', cols)
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='events';")
print('table_sql:', cur.fetchone())
conn.close()
