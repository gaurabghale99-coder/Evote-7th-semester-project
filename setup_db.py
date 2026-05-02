import psycopg2
# Connect to Supabase Cloud Database
conn_params = {
    "host": "localhost",
    "dbname": "evote",
    "user": "postgres",
    "password": "gaurab4445",
    "port": 5432
}

try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    # Create voters table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            id SERIAL PRIMARY KEY,
            voter_id VARCHAR(50) UNIQUE NOT NULL,
            full_name VARCHAR(100),
            face_encoding FLOAT8[],
            voted BOOLEAN DEFAULT FALSE,
            date_of_birth DATE,
            parliamentary_constituency VARCHAR(100),
            blocked_until TIMESTAMP
        )
    """)
    
    # Create behavior_logs table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS behavior_logs (
            id SERIAL PRIMARY KEY,
            voter_id VARCHAR(50),
            timestamp FLOAT8,
            confidence FLOAT8,
            multiple_faces BOOLEAN
        )
    """)
    conn.commit()
    print("Cloud database tables 'voters' and 'behavior_logs' checked/created successfully.")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error connecting to Cloud Database: {e}")
