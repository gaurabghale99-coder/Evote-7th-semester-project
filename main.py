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
        
        # Load known encodings once
        self.known_encodings = []
        self.voters = []
        self.load_voters()
        
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def start_camera(self):
        with self.lock:
            self.active_users += 1
            if self.cap is None:
                print("Opening camera hardware...")
                self.cap = cv2.VideoCapture(0)

    def stop_camera(self):
        with self.lock:
            self.active_users = max(0, self.active_users - 1)
            if self.active_users == 0 and self.cap is not None:
                print("Releasing camera hardware...")
                self.cap.release()
                self.cap = None
                self.latest_frame = None

    def load_voters(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT id, voter_id, full_name, face_encoding, voted FROM voters")
            rows = cur.fetchall()
            for vid, code, name, enc, voted in rows:
                if enc:
                    self.known_encodings.append(np.array(enc))
                    self.voters.append({
                        "id": vid, "code": code, "name": name, "voted": voted
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
                            encs = face_recognition.face_encodings(rgb_small_converted, face_locations)
                            if encs:
                                dists = face_recognition.face_distance(self.known_encodings, encs[0])
                                if len(dists) > 0:
                                    idx = np.argmin(dists)
                                    if dists[idx] <= TOLERANCE:
                                        res = self.voters[idx].copy()
                                        res["voted"] = get_voter_voted_status(res["code"])
                                        self.recognition_result = res

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

# Global manager instance
manager = CameraManager()

# Generate MJPEG frames for streaming
def gen_frames():
    manager.start_camera()
    try:
        while True:
            if manager.latest_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + manager.latest_frame + b'\r\n')
            time.sleep(0.05)
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

# Get all registered voters
def get_all_voters():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT voter_id, full_name, date_of_birth, parliamentary_constituency FROM voters ORDER BY id ASC")
        rows = cur.fetchall()
        
        voters = []
        for row in rows:
            voters.append({
                "voter_id": row[0],
                "full_name": row[1],
                "date_of_birth": str(row[2]),
                "parliamentary_constituency": row[3]
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
