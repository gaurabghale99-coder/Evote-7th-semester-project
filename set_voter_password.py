#!/usr/bin/env python3
"""Utility to set (or reset) a password for a voter identified by email.

Usage:
    python3 set_voter_password.py <email> <new_password>

The script hashes the password with bcrypt and updates the `password_hash`
column in the `voters` table.
"""

import sys
import bcrypt
import psycopg2

# Database connection settings – keep in sync with backend.py
DB_CONFIG = {
    "host": "localhost",
    "dbname": "evote",
    "user": "postgres",
    "password": "gaurab4445",
    "port": 5432,
}

def set_password(email: str, password: str):
    pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "UPDATE voters SET password_hash = %s WHERE email = %s",
            (pwd_hash, email)
        )
        if cur.rowcount == 0:
            print(f"[!] No voter found with email: {email}")
        else:
            conn.commit()
            print(f"[+] Password updated for {email}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 set_voter_password.py <email> <new_password>")
        sys.exit(1)
    _, email_arg, pwd_arg = sys.argv
    set_password(email_arg, pwd_arg)
