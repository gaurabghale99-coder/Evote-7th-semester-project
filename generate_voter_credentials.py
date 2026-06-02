import psycopg2
import bcrypt
import os
import secrets
import string

# DB connection config – adjust if needed
DB_CONFIG = {
    "host": "localhost",
    "dbname": "evote",
    "user": "postgres",
    "password": "gaurab4445",
    "port": 5432,
}

def generate_password(length: int = 12) -> str:
    """Generate a strong random password.
    Includes upper, lower, digits, and symbols.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    # Ensure at least one of each category
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd)
                and any(c.isdigit() for c in pwd) and any(c in "!@#$%^&*()-_=+" for c in pwd)):
            return pwd

def hash_password(plain: str) -> str:
    # bcrypt expects bytes; use 12 rounds (default)
    hashed = bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    # Ensure password_hash column exists (run migration if needed)
    cur.execute("ALTER TABLE voters ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);")
    conn.commit()

    # Fetch all voters
    cur.execute("SELECT voter_id, email FROM voters;")
    voters = cur.fetchall()
    credentials = []
    for voter_id, email in voters:
        pwd = generate_password()
        pwd_hash = hash_password(pwd)
        cur.execute(
            "UPDATE voters SET password_hash = %s WHERE voter_id = %s",
            (pwd_hash, voter_id),
        )
        credentials.append((email, pwd))
    conn.commit()
    cur.close()
    conn.close()

    # Write credentials to a safe local file (do not commit to repo)
    out_path = os.path.join(os.path.dirname(__file__), "voter_credentials.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Voter email and generated password (for login)\n")
        for email, pwd in credentials:
            f.write(f"{email}: {pwd}\n")
    print(f"Generated credentials for {len(credentials)} voters and saved to {out_path}")

if __name__ == "__main__":
    main()
