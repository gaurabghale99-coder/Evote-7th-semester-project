import psycopg2

DB_CONFIG = {
    "dbname": "evote",
    "user": "postgres",
    "password": "gaurab4445",
    "host": "localhost",
    "port": "5432"
}

def reset_votes():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("UPDATE voters SET voted = FALSE")
        rows = cur.rowcount
        conn.commit()
        
        print(f"Successfully reset 'voted' status for {rows} voters.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error resetting database: {e}")

if __name__ == "__main__":
    confirm = input("Are you sure you want to reset ALL votes to FALSE? (y/n): ")
    if confirm.lower() == 'y':
        reset_votes()
    else:
        print("Operation cancelled.")
