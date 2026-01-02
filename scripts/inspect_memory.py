import sqlite3
import json
import os

db_path = r"d:\AGL\repo-copy\Core_Memory\memory.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit()

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check table schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    # Assuming table name is 'events' or similar based on ConsciousBridge code (I didn't see the table creation code, but I'll guess 'events' or 'ltm')
    # Let's check the schema of the first table found
    if tables:
        table_name = tables[0][0]
        print(f"Schema of {table_name}:")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
        # Query recent events
        print(f"\n--- Recent Events in {table_name} ---")
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY ts DESC LIMIT 10")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
            
        # Query for structural evolution
        print(f"\n--- Structural Evolution / Defining Events ---")
        cursor.execute(f"SELECT * FROM {table_name} WHERE type='defining' OR payload LIKE '%structural_evolution%' OR payload LIKE '%Self-Engineer%' ORDER BY ts DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"TS: {row[1]}")
            print(f"Type: {row[2]}")
            try:
                payload = json.loads(row[3])
                print(f"Payload: {json.dumps(payload, indent=2)}")
            except:
                print(f"Payload (raw): {row[3]}")
            print("-" * 20)
        
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
