import face_recognition
import numpy as np

# Load the voter's image
image = face_recognition.load_image_file("faces/voter1.jpg")

# Extract face encodings
encodings = face_recognition.face_encodings(image)

if len(encodings) == 0:
    print("No face detected in the image!")
else:
    # Save the encoding for future verification
    voter_encoding = encodings[0]
    np.save("faces/voter1_encoding.npy", voter_encoding)
    print("Face registered successfully!")
