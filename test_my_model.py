# test_my_model.py
# Test your custom-trained face recognition model with live webcam

import cv2
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
import face_recognition

print("=" * 50)
print("  TESTING YOUR CUSTOM FACE MODEL")
print("=" * 50)
print()

# Load class names
with open("face_model_classes.txt", "r") as f:
    class_names = [line.strip() for line in f.readlines()]
print(f"📋 Known voters: {class_names}")

# Rebuild the same model architecture
model = models.resnet18(pretrained=False)
model.fc = nn.Sequential(
    nn.Linear(512, 256),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Linear(128, len(class_names))
)

# Load your trained weights
checkpoint = torch.load("my_face_model.pth", map_location="cpu")
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()
print("✅ Model loaded!")

# --- DB ENCODINGS FOR HYBRID VERIFICATION ---
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "dbname": "evote",
    "user": "postgres",
    "password": "gaurab4445",
    "port": 5432
}

known_voter_encodings = {}
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT voter_id, face_encoding FROM voters WHERE face_encoding IS NOT NULL")
    for row in cur.fetchall():
        voter_id, enc = row
        known_voter_encodings[voter_id.strip().lower()] = np.array(enc)
    cur.close()
    conn.close()
    print(f"Loaded {len(known_voter_encodings)} face encodings from database for hybrid verification.")
except Exception as e:
    print(f"⚠️ Warning: Could not connect to database: {e}")
    print("Verification will fall back to model confidence only.")
# ---------------------------------------------

# Image preprocessing (same as training)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: Cannot open camera!")
    exit(1)

print()
print("==========================================")
print("  Camera is live! Press Q to quit.")
print("==========================================")
print()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Compress frame to 1/4 size for super-fast face detection (fixes the lag!)
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    
    boxes = face_recognition.face_locations(rgb_small)
    
    if len(boxes) > 0:
        # Get the first face and scale coordinates back up by 4
        top, right, bottom, left = boxes[0]
        top *= 4; right *= 4; bottom *= 4; left *= 4
        
        # Add 20% margin
        h = bottom - top; w = right - left
        mt = max(0, top - int(h*0.2)); mb = min(frame.shape[0], bottom + int(h*0.2))
        ml = max(0, left - int(w*0.2)); mr = min(frame.shape[1], right + int(w*0.2))
        
        # Crop to face
        face_crop = frame[mt:mb, ml:mr]
        face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        
        # Prepare for AI
        pil_img = Image.fromarray(face_rgb)
        tensor = transform(pil_img).unsqueeze(0)

        # Predict
        with torch.no_grad():
            outputs = model(tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
            
            name = class_names[predicted.item()]
            conf = confidence.item() * 100

        # Calculate live face encoding for verification
        is_verified = False
        dist_str = ""
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        live_encodings = face_recognition.face_encodings(rgb_frame, [(top, right, bottom, left)])
        if len(live_encodings) > 0 and len(known_voter_encodings) > 0:
            live_enc = live_encodings[0]
            target_id = name.split('_')[0].strip().lower()
            db_enc = known_voter_encodings.get(target_id)
            if db_enc is not None:
                # Compute distance (smaller = closer match)
                dist = face_recognition.face_distance([db_enc], live_enc)[0]
                dist_str = f" | Dist: {dist:.2f}"
                # 0.42 is a strict threshold to completely prevent stranger matches (smaller is stricter)
                if dist < 0.42:
                    is_verified = True
        else:
            # Fallback to confidence check if DB encodings are missing
            if conf > 85:
                is_verified = True

        # Draw result on frame
        if is_verified and conf > 85:
            color = (0, 255, 0)  # Green = recognized voter
            label = f"{name}: {conf:.1f}%{dist_str}"
        else:
            color = (0, 0, 255)  # Red = unknown stranger
            label = f"UNKNOWN STRANGER: {conf:.1f}%{dist_str}"

        # Draw a box around the face
        cv2.rectangle(frame, (ml, mt), (mr, mb), color, 2)
        cv2.putText(frame, label, (ml, mt - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    else:
        cv2.putText(frame, "No face detected", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("Custom Face Model Test", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Test complete!")
