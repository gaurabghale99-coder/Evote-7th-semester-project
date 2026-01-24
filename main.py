# main.py
import cv2
import face_recognition
import numpy as np
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "dbname": "evote",
    "user": "postgres",
    "password": "gaurab4445",
    "port": 5432
}

TOLERANCE = 0.45  # smaller = stricter match

# Recognize face once using webcam
def recognize_face_once():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT id, voter_code, name, face_encoding, voted FROM voters")
    rows = cur.fetchall()

    known_encodings = []
    voters = []

    for vid, code, name, enc, voted in rows:
        if enc:
            known_encodings.append(np.array(enc))
            voters.append({
                "id": vid,
                "code": code,
                "name": name,
                "voted": voted
            })

    cap = cv2.VideoCapture(0)
    result = None

    for _ in range(60):  # 60 frames to try
        ret, frame = cap.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encs = face_recognition.face_encodings(rgb)

        if len(encs) != 1:
            continue

        dists = face_recognition.face_distance(known_encodings, encs[0])
        idx = np.argmin(dists)

        if dists[idx] <= TOLERANCE:
            result = voters[idx]
            break

    cap.release()
    cur.close()
    conn.close()
    return result

# Mark voter as voted
def mark_as_voted(voter_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT voted FROM voters WHERE id=%s", (voter_id,))
    row = cur.fetchone()

    if not row or row[0]:
        return False

    cur.execute("UPDATE voters SET voted=TRUE WHERE id=%s", (voter_id,))
    conn.commit()
    cur.close()
    conn.close()
    return True
