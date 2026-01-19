import face_recognition
import numpy as np

# Load stored encoding
known_encoding = np.load("faces/voter1_encoding.npy")

# Load the live image (the person trying to vote)
live_image = face_recognition.load_image_file("faces/live.jpg")
live_encodings = face_recognition.face_encodings(live_image)

if len(live_encodings) == 0:
    print("No face detected in the live image!")
    exit()

live_encoding = live_encodings[0]

# Compare faces
results = face_recognition.compare_faces([known_encoding], live_encoding, tolerance=0.5)
distance = face_recognition.face_distance([known_encoding], live_encoding)

if results[0]:
    print("VERIFIED")
    print("Confidence:", round((1 - distance[0]) * 100, 2), "%")
else:
    print("NOT VERIFIED")
