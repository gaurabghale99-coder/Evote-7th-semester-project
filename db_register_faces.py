import psycopg2
import face_recognition
import os
import numpy as np

DB_CONFIG = {
    "host": "db.jbmtnxzfdhsrpyyhyybt.supabase.co",
    "dbname": "postgres",
    "user": "postgres",
    "password": "gaurab@4445",
    "port": 5432
}

FACES_DIR = "faces"

def register_faces():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Get last voter_id formatted Vxxx
        cur.execute("SELECT voter_id FROM voters WHERE voter_id LIKE 'V%' ORDER BY voter_id DESC LIMIT 1")
        row = cur.fetchone()
        
        # Determine starting counter
        if row and row[0]:
            try:
                counter = int(row[0][1:]) + 1
            except ValueError:
                counter = 1
        else:
            counter = 1

        files = sorted(os.listdir(FACES_DIR))
        registered_count = 0
        updated_count = 0

        for file in files:
            if not file.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            # Full name is filename without extension (initially)
            name_from_file = os.path.splitext(file)[0].lower()
            path = os.path.join(FACES_DIR, file)

            print(f"Processing {file}...")
            
            try:
                img = face_recognition.load_image_file(path)
                encs = face_recognition.face_encodings(img)
            except Exception as e:
                print(f"  Error loading {file}: {e}")
                continue

            if len(encs) != 1:
                print(f"  Skipping {file}: Found {len(encs)} faces (expected 1).")
                continue

            encoding = encs[0].tolist()

            # Check if voter already exists by name (case insensitive)
            # We check if full_name contains the name_from_file
            cur.execute("SELECT voter_id, full_name FROM voters WHERE LOWER(full_name) LIKE %s OR LOWER(full_name) = %s", 
                        (f"%{name_from_file}%", name_from_file))
            existing = cur.fetchone()

            if existing:
                v_id, full_name = existing
                print(f"  Updating existing voter: {full_name} ({v_id})")
                cur.execute("""
                    UPDATE voters SET face_encoding = %s WHERE voter_id = %s
                """, (encoding, v_id))
                updated_count += 1
            else:
                new_voter_id = f"V{counter:03d}"
                print(f"  Registering NEW voter: {name_from_file} as {new_voter_id}")
                cur.execute("""
                    INSERT INTO voters (voter_id, full_name, face_encoding, voted)
                    VALUES (%s, %s, %s, FALSE)
                """, (new_voter_id, name_from_file, encoding))
                counter += 1
                registered_count += 1

        conn.commit()
        cur.close()
        conn.close()
        print(f"\nFace registration summary:")
        print(f"  New voters registered: {registered_count}")
        print(f"  Existing voters updated: {updated_count}")
        
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    register_faces()

