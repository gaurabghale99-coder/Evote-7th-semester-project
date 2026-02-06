import psycopg2
import face_recognition
import os

conn = psycopg2.connect(
    dbname="evote",
    user="postgres",
    password="gaurab4445",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

FACES_DIR = "faces"

# Get last voter_code number
cur.execute("SELECT voter_id FROM voters ORDER BY voter_id DESC LIMIT 1")
row = cur.fetchone()
counter = int(row[0][1:]) + 1 if row and row[0] and row[0].startswith('V') else 1

for file in sorted(os.listdir(FACES_DIR)):
    if not file.lower().endswith(".jpg"):
        continue

    name = os.path.splitext(file)[0].lower()
    path = os.path.join(FACES_DIR, file)

    img = face_recognition.load_image_file(path)
    encs = face_recognition.face_encodings(img)

    if len(encs) != 1:
        continue

    voter_id = f"V{counter:03d}"
    counter += 1

    # Insert without ON CONFLICT, since names can repeat
    cur.execute("""
        INSERT INTO voters (voter_id, full_name, face_encoding, voted)
        VALUES (%s, %s, %s, FALSE)
    """, (voter_id, name, encs[0].tolist()))

conn.commit()
cur.close()
conn.close()

print("Face registration complete")
