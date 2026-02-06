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
    cur.execute("SELECT id, voter_id, full_name, date_of_birth, voted FROM voters")
    rows = cur.fetchall()
    print("Voters in DB:")
    for row in rows:
        print(f"ID: {row[0]}, VoterID: {row[1]}, Name: {row[2]}, DOB: {row[3]} ({type(row[3])}), Voted: {row[4]} ({type(row[4])})")
    
    cur.execute("SELECT date_of_birth FROM voters WHERE voted = TRUE")
    voted_rows = cur.fetchall()
    print(f"\nVoted count with explicit TRUE: {len(voted_rows)}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
