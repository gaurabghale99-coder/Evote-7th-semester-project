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


def add_email_column_and_backfill():
    """Add a unique email column to voters and populate placeholder emails."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Add column if it doesn't exist
        cur.execute("ALTER TABLE voters ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;")
        # Backfill placeholder emails for rows where email is NULL
        cur.execute("SELECT voter_id FROM voters WHERE email IS NULL;")
        rows = cur.fetchall()
        for (voter_id,) in rows:
            placeholder = f'voter{voter_id}@example.com'
            cur.execute(
                "UPDATE voters SET email = %s WHERE voter_id = %s",
                (placeholder, voter_id)
            )
        conn.commit()
        cur.close()
        conn.close()
        print("Email column added and backfilled successfully.")
    except Exception as e:
        print(f"Error adding email column: {e}")

if __name__ == "__main__":
    add_blocked_until_column()
    add_email_column_and_backfill()
