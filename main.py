import cv2
import face_recognition
import numpy as np
import os
import json
from scipy.spatial import distance as dist

# ---------- Paths ----------
FACES_DIR = "faces"
DATA_FILE = "data/voters.json"

# ---------- Load voter data ----------
with open(DATA_FILE, "r") as f:
    voters = json.load(f)

# ---------- Load and encode known faces ----------
known_face_encodings = []
known_face_names = []

for file in os.listdir(FACES_DIR):
    if not file.lower().endswith(".jpg"):
        continue
    name = os.path.splitext(file)[0]
    image_path = os.path.join(FACES_DIR, file)
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    if len(encodings) != 1:
        print(f"Skipped {file} (no face or multiple faces)")
        continue
    known_face_encodings.append(encodings[0])
    known_face_names.append(name)

print("Loaded faces:", known_face_names)

# ---------- Helper functions ----------
def eye_aspect_ratio(eye):
    # Compute EAR to detect blink
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# ---------- Start camera ----------
cap = cv2.VideoCapture(0)
MAX_ATTEMPTS = 3
EAR_THRESHOLD = 0.2  # Eye blink threshold
blink_detected = False
head_direction = None  # None, 'left', 'right'

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    message = "NO FACE"
    color = (0, 0, 255)

    # Multiple faces = reject
    if len(face_encodings) > 1:
        message = "REJECTED: MULTIPLE FACES"
        color = (0, 0, 255)
    elif len(face_encodings) == 1:
        face_encoding = face_encodings[0]
        matches = face_recognition.compare_faces(
            known_face_encodings, face_encoding, tolerance=0.5
        )
        name = "UNKNOWN"
        top, right, bottom, left = face_locations[0]

        # Draw green rectangle around face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        if True in matches:
            match_index = matches.index(True)
            name = known_face_names[match_index]
            voter = voters.get(name)

            # ---------------- Blink and head turn liveness check ----------------
            # Convert to grayscale for simple landmark approximation
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_center_x = (left + right) // 2

            # Head movement detection
            if face_center_x < frame.shape[1] // 3:
                head_direction = 'left'
            elif face_center_x > 2 * frame.shape[1] // 3:
                head_direction = 'right'
            else:
                head_direction = 'center'

            # Liveness rule: user must move head left & right (at least once)
            if head_direction in ['left', 'right']:
                head_moved = True
            else:
                head_moved = False

            # Decision logic
            if voter["attempts"] >= MAX_ATTEMPTS:
                message = "REJECTED: TOO MANY ATTEMPTS"
                color = (0, 0, 255)
            elif voter["voted"]:
                message = "ALREADY VOTED"
                color = (0, 255, 255)
            elif head_moved:
                # Accept if head moved
                voter["voted"] = True
                voter["attempts"] = 0
                message = f"ACCEPTED: {name}"
                color = (0, 255, 0)
                with open(DATA_FILE, "w") as f:
                    json.dump(voters, f, indent=4)
            else:
                voter["attempts"] += 1
                message = "MOVE HEAD LEFT/RIGHT"
                color = (0, 0, 255)

        else:
            # Unknown face attempt
            message = "NOT ACCEPTED"
            color = (0, 0, 255)

    # Draw status message
    cv2.putText(frame, message, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    cv2.imshow("Face Lock Voting System", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
