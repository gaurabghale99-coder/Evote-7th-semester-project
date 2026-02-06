import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "dbname": "evote",
    "user": "postgres",
    "password": "gaurab4445",
    "port": 5432
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'voters'")
    columns = cur.fetchall()
    print("Columns in 'voters' table:")
    for col in columns:
        print(f"- {col[0]}")
    
    cur.execute("SELECT id, face_encoding IS NOT NULL as has_encoding, voted FROM voters")
    rows = cur.fetchall()
    print("\nRows in 'voters' table:")
    for row in rows:
        print(row)
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
