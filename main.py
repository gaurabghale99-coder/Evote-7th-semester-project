# main.py

import os
import cv2
import numpy as np
# Import the anti-spoofing module you copied from the src folder
from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from src.utility import parse_model_name
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

# Initialize the anti-spoofing model
anti_spoof_model = AntiSpoofPredict(device_id=0)
image_cropper = CropImage()

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

TOLERANCE = 0.42  # smaller = stricter match
FRAUD_THRESHOLD = 0.06 # Change this to 0.7 for production. Lower = easier to trigger fraud warning.

import threading
import time

# Camera Manager to handle all hardware and detection in one thread
class CameraManager:
    def __init__(self):
        self.cap = None
        self.latest_frame = None
        self.recognition_result = None
        self.multiple_faces_detected = False
        self.running = True
        self.active_users = 0 # Count of how many things currently need the camera
        self.lock = threading.Lock()
        
        # --- CUSTOM MODEL SETUP ---
        # Load class names
        with open("face_model_classes.txt", "r") as f:
            self.class_names = [line.strip() for line in f.readlines()]
            
        # Rebuild the custom ResNet-18 architecture
        self.custom_model = models.resnet18(pretrained=False)
        self.custom_model.fc = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, len(self.class_names))
        )
        
        # Load weights
        checkpoint = torch.load("my_face_model.pth", map_location="cpu")
        self.custom_model.load_state_dict(checkpoint['model_state_dict'])
        self.custom_model.eval()
        
        # Image transformation for the custom model
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        # --------------------------

        # Load known encodings (kept for database reference, but recognition uses classifier)
        self.known_encodings = []
        self.voters = []
        self.load_voters()
        
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def start_camera(self):
        with self.lock:
            self.active_users += 1
            print(f"Camera start requested. Active users: {self.active_users}")
            if self.cap is None:
                print("Opening camera hardware...")
                self.cap = cv2.VideoCapture(0)
                # Wait a moment for camera to warm up
                time.sleep(0.5)

    def stop_camera(self):
        with self.lock:
            if self.active_users > 0:
                self.active_users -= 1
            print(f"Camera stop requested. Active users: {self.active_users}")
            if self.active_users == 0 and self.cap is not None:
                print("Releasing camera hardware...")
                self.cap.release()
                self.cap = None
                self.latest_frame = None
                self.recognition_result = None
                self.multiple_faces_detected = False

    def force_stop(self):
        with self.lock:
            print("Force stopping camera...")
            self.active_users = 0
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                self.latest_frame = None
                self.recognition_result = None
                self.multiple_faces_detected = False

    def load_voters(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT id, voter_id, full_name, face_encoding, voted FROM voters")
            rows = cur.fetchall()
            for vid, code, name, enc, voted in rows:
                if enc:
                    enc_arr = np.array(enc)
                    self.known_encodings.append(enc_arr)
                    self.voters.append({
                        "id": vid, "code": code, "name": name, "voted": voted, "face_encoding": enc_arr
                    })
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error loading voters: {e}")

    def _run(self):
        while self.running:
            try:
                # Use a local reference to avoid None issues, but still check under lock
                with self.lock:
                    if self.cap is None:
                        cap_is_none = True
                    else:
                        cap_is_none = False
                
                if cap_is_none:
                    time.sleep(0.1)
                    continue

                # Perform the read operation while holding the lock to prevent simultaneous release
                with self.lock:
                    if self.cap is None:
                        continue
                    success, frame = self.cap.read()

                if not success or frame is None:
                    time.sleep(0.1)
                    continue

            # 1. Detect faces for the live green rectangle (Low res for speed)
                rgb_small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                # Use color conversion for face_recognition library
                rgb_small_converted = cv2.cvtColor(rgb_small, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_small_converted)

                # 2. STRICT CHECK: If multiple faces detected at ANY point, invalidate everything
                if self.active_users > 0:
                    if len(face_locations) > 1:
                        # Multiple faces detected - IMMEDIATELY set error and invalidate any previous result
                        self.multiple_faces_detected = True
                        self.recognition_result = {"multiple_faces": True}
                    elif len(face_locations) == 1 and not self.recognition_result:
                        # Only proceed with recognition if:
                        # 1. Exactly one face is present
                        # 2. No result has been set yet
                        # 3. Multiple faces have NOT been detected previously in this session
                        if not self.multiple_faces_detected:
                            # --- ANTI-SPOOFING LIVENESS CHECK ---
                            # Get the face location coordinates (scaled back to original frame size)
                            top, right, bottom, left = face_locations[0]
                            top *= 4
                            right *= 4
                            bottom *= 4
                            left *= 4
                            
                            # ACTUALLY expand the crop so the anti-spoof model sees the phone edges/background
                            w = right - left
                            h = bottom - top
                            
                            # Expand by 50% on each side
                            expand_w = int(w * 0.5)
                            expand_h = int(h * 0.5)
                            
                            new_left = max(0, left - expand_w)
                            new_top = max(0, top - expand_h)
                            new_right = min(frame.shape[1], right + expand_w)
                            new_bottom = min(frame.shape[0], bottom + expand_h)
                            
                            image_bbox = [new_left, new_top, new_right - new_left, new_bottom - new_top]
                            
                            prediction = np.zeros((1, 3))
                            is_real = False
                            score = 0.0
                            encs = None  # IMPORTANT: Reset encodings every frame!
                            try:
                                for model_name in os.listdir("anti_spoof_models"):
                                    model_path = os.path.join("anti_spoof_models", model_name)
                                    h_input, w_input, model_type, scale = parse_model_name(model_name)
                                    param = {
                                        "org_img": frame,
                                        "bbox": image_bbox,
                                        "scale": scale,
                                        "out_w": w_input,
                                        "out_h": h_input,
                                        "crop": True,
                                    }
                                    if scale is None:
                                        param["crop"] = False
                                        
                                    img = image_cropper.crop(**param)
                                    prediction += anti_spoof_model.predict(img, model_path)
                                    
                                label = np.argmax(prediction)
                                score = prediction[0][label] / 2.0  # Because there are 2 models
                                is_real = (label == 1 and score > 0.95)
                            except Exception as e:
                                print(f"Spoof detection error: {e}")
                                
                            if not is_real:
                                print(f"❌ SPOOF DETECTED! Score: {score:.2f}")
                                cv2.putText(frame, "SPOOF DETECTED!", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                                # Do not run face recognition! encs stays None
                            if is_real:
                                # 1. Prepare face crop for custom model
                                face_crop = frame[new_top:new_bottom, new_left:new_right]
                                face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                                pil_img = Image.fromarray(face_rgb)
                                tensor = self.transform(pil_img).unsqueeze(0)
                                
                                # 2. Run prediction using your SELF-TRAINED model
                                with torch.no_grad():
                                    outputs = self.custom_model(tensor)
                                    probabilities = torch.nn.functional.softmax(outputs, dim=1)
                                    confidence, predicted = torch.max(probabilities, 1)
                                    
                                    recognized_name = self.class_names[predicted.item()]
                                    conf_score = confidence.item() * 100
                                    
                                print(f"🤖 Custom AI Result: {recognized_name} ({conf_score:.1f}%)")
                                # We consider a face "known" only if:
                                #   1. The model predicts a class with sufficient confidence (>85) AND
                                #   2. The corresponding voter exists in DB AND
                                #   3. The live face encoding distance is below TOLERANCE.
                                # Otherwise we label as UNKNOWN STRANGER.
                                if conf_score > 85:
                                    target_id = recognized_name.split('_')[0].strip().lower()
                                    matched_voter = next((v for v in self.voters if v['code'].strip().lower() == target_id), None)
                                    
                                    if matched_voter:
                                        # Secondary Distance Verification
                                        is_verified = False
                                        db_enc = matched_voter.get("face_encoding")
                                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                        live_encs = face_recognition.face_encodings(rgb_frame, [(top, right, bottom, left)])
                                        if len(live_encs) > 0 and db_enc is not None:
                                            live_enc = live_encs[0]
                                            dist = face_recognition.face_distance([db_enc], live_enc)[0]
                                            print(f"🔗 Hybrid Verification - Predicted: {matched_voter['name']} | Distance: {dist:.4f}")
                                            if dist < TOLERANCE:
                                                is_verified = True
                                        else:
                                            # Fallback to confidence if encoding check fails
                                            is_verified = True
                                            
                                        if is_verified:
                                            res = matched_voter.copy()
                                            res["voted"] = get_voter_voted_status(res["code"])
                                            
                                            # --- RNN Behavior Analysis ---
                                            from behavior_tracker import BehaviorTracker
                                            tracker = BehaviorTracker(DB_CONFIG)
                                            # Use AI confidence for RNN score
                                            fraud_score = tracker.log_attempt(res["code"], confidence.item(), False)
                                            res["fraud_score"] = fraud_score
                                            res["is_suspicious"] = fraud_score > FRAUD_THRESHOLD
                                            
                                            # Save last fraud score to database
                                            save_last_fraud_score(res["code"], fraud_score)
                                            
                                            print(f"--- Behavioral Analysis RNN ---")
                                            print(f"Voter ID: {res['code']}")
                                            print(f"Fraud Score: {fraud_score:.4f}")
                                            print(f"Status: {'⚠️ SUSPICIOUS' if res['is_suspicious'] else '✅ NORMAL'}")
                                            print(f"-------------------------------")
                                            
                                            self.recognition_result = res
                                            
                                            if res.get("is_suspicious"):
                                                record_voter_block(res["code"], 1, fraud_score)
                                        else:
                                            print(f"❌ Hybrid check failed! Dist too high. Not matching {matched_voter['name']}")
                                    else:
                                        print(f"⚠️ Recognized as {recognized_name} but ID not in Voter DB.")
                                else:
                                    print(f"❓ UNKNOWN STRANGER (Conf: {conf_score:.1f}%)")
                    elif len(face_locations) > 1:
                         # Extra check for multiple faces under RNN
                         from behavior_tracker import BehaviorTracker
                         tracker = BehaviorTracker(DB_CONFIG)
                         tracker.log_attempt("ANONYMOUS", 0.0, True) 

                # 3. Draw green rectangles ALWAYS for feedback
                for (top, right, bottom, left) in face_locations:
                    # Scale back up by 4 since we resized to 0.25
                    top *= 4; right *= 4; bottom *= 4; left *= 4
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

                # 4. Store latest frame for streaming
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    self.latest_frame = buffer.tobytes()

                # Small sleep to keep CPU usage in check
                time.sleep(0.01)
            except Exception as e:
                print(f"Error in camera loop: {e}")
                time.sleep(0.5) # Wait a bit before retrying if there's an error

# Helper to check latest voted status
def get_voter_voted_status(voter_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT voted FROM voters WHERE voter_id = %s", (voter_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else False
    except Exception as e:
        print(f"Error checking voted status: {e}")
        return False

# Record a block for a voter for N minutes
def record_voter_block(voter_id, minutes=1, fraud_score=0.0):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Calculate block time and save fraud score
        cur.execute("""
            UPDATE voters 
            SET blocked_until = NOW() + INTERVAL '%s minutes',
                last_fraud_score = %s
            WHERE voter_id = %s
        """, (minutes, fraud_score, voter_id))
        conn.commit()
        cur.close()
        conn.close()
        print(f"Voter {voter_id} blocked for {minutes} minute(s). Score: {fraud_score}")
    except Exception as e:
        print(f"Error recording voter block: {e}")

# Helper to save last fraud score without blocking
def save_last_fraud_score(voter_id, fraud_score):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("UPDATE voters SET last_fraud_score = %s WHERE voter_id = %s", (fraud_score, voter_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error saving fraud score: {e}")

# Check if voter is currently blocked
def is_voter_blocked(voter_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT blocked_until > NOW() FROM voters WHERE voter_id = %s", (voter_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row and row[0] is not None else False
    except Exception as e:
        print(f"Error checking blocked status: {e}")
        return False

# Newly added: Verify voter ID and DOB for registration
def verify_voter_details(voter_id, full_name, dob):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # We fetch the record for the voter_id
        cur.execute("SELECT full_name, date_of_birth, voted FROM voters WHERE voter_id = %s", (voter_id,))
        record = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if record is None:
            return {"verified": False, "message": "Voter ID not found in database."}
        
        db_name, db_dob, db_voted = record

        if db_voted:
             return {"verified": False, "message": "You have already voted."}
        
        # Case insensitive name check (optional but helpful)
        if db_name.strip().lower() != full_name.strip().lower():
             return {"verified": False, "message": "Full Name does not match our records."}

        # Date of Birth check
        # db_dob might be a date object or a string depending on the schema
        # Based on update_schema.py it's TIMESTAMP, but the screenshot showed 'character varying'
        # Let's handle both.
        db_dob_str = str(db_dob).strip()
        input_dob_str = dob.strip()
        
        # Standardize format for comparison (YYYY/MM/DD vs YYYY-MM-DD)
        db_dob_std = db_dob_str.replace('-', '/')
        input_dob_std = input_dob_str.replace('-', '/')
        
        if db_dob_std != input_dob_std:
            return {"verified": False, "message": "Incorrect Date of Birth."}
            
        return {"verified": True}
        
    except Exception as e:
        print(f"Error verifying voter details: {e}")
        return {"verified": False, "message": "An error occurred during verification."}

# Newly added: Get voter's parliamentary constituency
def get_voter_constituency(voter_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT parliamentary_constituency FROM voters WHERE voter_id = %s", (voter_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Error fetching constituency: {e}")
        return None

# Global manager instance
manager = CameraManager()

# Generate MJPEG frames for streaming
def gen_frames():
    manager.start_camera()
    try:
        # Wait up to 2 seconds for the first valid frame to avoid "black box" issue
        start_wait = time.time()
        while manager.latest_frame is None and time.time() - start_wait < 2:
            time.sleep(0.1)
            
        while True:
            with manager.lock:
                if manager.cap is None or manager.active_users == 0:
                    break
            
            if manager.latest_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + manager.latest_frame + b'\r\n')
            time.sleep(0.04) # ~25 FPS
    finally:
        manager.stop_camera()

# Recognize face once using the background result
def recognize_face_once():
    # Signal that we need the camera for recognition
    manager.start_camera()
    manager.recognition_result = None
    manager.multiple_faces_detected = False  # Reset flag for new attempt
    
    try:
        start_time = time.time()
        while time.time() - start_time < 10:
            if manager.recognition_result:
                return manager.recognition_result
            time.sleep(0.1)
    finally:
        manager.stop_camera()
        
    return None

# Mark voter as voted
def mark_as_voted(voter_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT voted FROM voters WHERE voter_id=%s", (voter_id,))
    row = cur.fetchone()

    if not row or row[0]:
        return False

    cur.execute("UPDATE voters SET voted=TRUE WHERE voter_id=%s", (voter_id,))
    conn.commit()
    cur.close()
    conn.close()
    return True

# Reset all voters status
def reset_all_voters():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("UPDATE voters SET voted=FALSE")
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error resetting voters: {e}")
        return False

# Get all registered voters
def get_all_voters():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT voter_id, full_name, date_of_birth, parliamentary_constituency, 
                   last_fraud_score, blocked_until, blocked_until > NOW() as is_blocked
            FROM voters 
            ORDER BY id ASC
        """)
        rows = cur.fetchall()
        
        voters = []
        for row in rows:
            voters.append({
                "voter_id": row[0],
                "full_name": row[1],
                "date_of_birth": str(row[2]),
                "parliamentary_constituency": row[3],
                "last_fraud_score": round(float(row[4] or 0.0), 4),
                "blocked_until": str(row[5]) if row[5] else None,
                "is_blocked": bool(row[6])
            })
        cur.close()
        conn.close()
        return voters
    except Exception as e:
        print(f"Error fetching voters: {e}")
        return []

# Get age group votes summary
def get_age_group_summary():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT date_of_birth FROM voters WHERE voted = TRUE")
        rows = cur.fetchall()
        
        summary = {
            "18-25": 0,
            "26-35": 0,
            "36-45": 0,
            "46-60": 0,
            "60 above": 0
        }
        
        current_bs_year = 2082
        
        for row in rows:
            dob_val = row[0]
            if not dob_val:
                continue
            try:
                dob_str = str(dob_val)
                year = int(dob_str[:4])
                age = current_bs_year - year
                
                if 18 <= age <= 25: summary["18-25"] += 1
                elif 26 <= age <= 35: summary["26-35"] += 1
                elif 36 <= age <= 45: summary["36-45"] += 1
                elif 46 <= age <= 60: summary["46-60"] += 1
                elif age > 60: summary["60 above"] += 1
            except (ValueError, IndexError):
                continue
                
        cur.close()
        conn.close()
        return summary
    except Exception as e:
        print(f"Error calculating age summary: {e}")
        return {}
