import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to 'postgres' db to create 'evote' db
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="gaurab4445",
    host="localhost",
    port="5432"
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

try:
    cur.execute("CREATE DATABASE evote")
    print("Database 'evote' created successfully.")
except psycopg2.errors.DuplicateDatabase:
    print("Database 'evote' already exists.")
except Exception as e:
    print(f"Error creating database: {e}")

cur.close()
conn.close()

# Now connect to 'evote' to create table
try:
    conn = psycopg2.connect(
        dbname="evote",
        user="postgres",
        password="gaurab4445",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    # Create voters table
    # face_encoding is stored as list in python, so likely FLOAT array in Postgres
    cur.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            id SERIAL PRIMARY KEY,
            voter_id VARCHAR(50) UNIQUE NOT NULL,
            full_name VARCHAR(100),
            face_encoding FLOAT8[],
            voted BOOLEAN DEFAULT FALSE,
            date_of_birth DATE,
            parliamentary_constituency VARCHAR(100)
        )
    """)
    conn.commit()
    print("Table 'voters' checked/created successfully.")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error creating table: {e}")
