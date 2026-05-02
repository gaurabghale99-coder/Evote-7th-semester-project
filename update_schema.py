import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "dbname": "evote",
    "user": "postgres",
    "password": "gaurab4445",
    "port": 5432
}

def add_blocked_until_column():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("ALTER TABLE voters ADD COLUMN IF NOT EXISTS blocked_until TIMESTAMP;")
        conn.commit()
        cur.close()
        conn.close()
        print("Column 'blocked_until' added successfully.")
    except Exception as e:
        print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_blocked_until_column()
