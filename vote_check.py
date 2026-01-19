import face_recognition
import os

FACES_DIR = r"C:\facerecognition\faces"

known_faces = []

def check_faces():
    for file in os.listdir(FACES_DIR):
        file_path = os.path.join(FACES_DIR, file)
        print(f"\nChecking {file}...")

        # 1. Not an image file
        if not file.lower().endswith((".jpg", ".jpeg", ".png")):
            print("ERROR: Not an image file. Please upload a face image.")
            continue

        # 2. Corrupted or unreadable image
        try:
            image = face_recognition.load_image_file(file_path)
        except Exception:
            print("ERROR: Image cannot be opened or is corrupted.")
            continue

        encodings = face_recognition.face_encodings(image)

        # 3. Image but no face
        if len(encodings) == 0:
            print("ERROR: No face detected. Please upload a clear face photo.")
            continue

        current_encoding = encodings[0]

        # 4. Same face as previous image
        if known_faces:
            distances = face_recognition.face_distance(known_faces, current_encoding)
            if distances.min() < 0.5:
                print("ERROR: Same face detected. Duplicate image not allowed.")
                continue

        # Valid new face
        known_faces.append(current_encoding)
        print("Valid face detected. Image accepted.")


# ---- RUN ----
check_faces()
