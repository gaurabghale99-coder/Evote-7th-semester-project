from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import time
import psycopg2

# Database connection settings – keep in sync with set_voter_password.py
DB_CONFIG = {
    "host": "localhost",
    "dbname": "evote",
    "user": "postgres",
    "password": "gaurab4445",
    "port": 5432,
}

from main import (
    recognize_face_once, mark_as_voted, gen_frames, 
    get_all_voters, get_age_group_summary, is_voter_blocked,
    verify_voter_details, get_voter_constituency
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security: Disable Browser Caching globally
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Record vote model
class VoteRecord(BaseModel):
    voter_id: str

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

# Face login endpoint
@app.get("/face_login")
def face_login():
    res = recognize_face_once()

    if not res:
        return {"status": "unknown"}
    
    # Check if multiple faces were detected
    if res.get("multiple_faces") is True:
        return {"status": "multiple_faces"}

    # Check if voter is blocked
    voter_code = res.get("code")

    # Check if already voted
    if res.get("voted"):
        return {"status": "already_voted", "name": res.get("name")}

    if voter_code and is_voter_blocked(voter_code):
        return {
            "status": "blocked",
            "message": "Fraud detected. Your voting is blocked for 1 minute."
        }

    return {
        "status": "allowed",
        "name": res.get("name"),
        "voter_id": res.get("id"),
        "voter_code": voter_code,
        "fraud_score": res.get("fraud_score", 0.0),
        "is_suspicious": res.get("is_suspicious", False)
    }

@app.post("/record_vote")
def record_vote(data: VoteRecord):
    # Prevent double voting via API check
    from main import get_voter_voted_status
    if get_voter_voted_status(data.voter_id):
         return {"status": "failed", "message": "You have already voted."}

    success = mark_as_voted(data.voter_id)
    if success:
        # In a real ATM system, we'd clear the backend session here
        # Since we are using stateless API + localStorage, the 'session' is cleared on the frontend.
        return {"status": "success"}
    return {"status": "failed", "message": "Could not record vote or already voted"}

@app.get("/reset_all_votes")
def reset_all_votes_endpoint():
    from main import reset_all_voters
    success = reset_all_voters()
    if success:
        return {"status": "success"}
    return {"status": "error", "message": "Failed to reset votes in DB"}

# New endpoint for DOB and name verification
class VoterVerification(BaseModel):
    voter_id: str
    full_name: str
    dob: str

@app.post("/verify_voter_details")
def verify_voter_endpoint(data: VoterVerification):
    result = verify_voter_details(data.voter_id, data.full_name, data.dob)
    return result

@app.get("/get_constituency")
def get_constituency_endpoint(voter_id: str):
    # Protection: Prevent access if already voted
    from main import get_voter_voted_status
    if get_voter_voted_status(voter_id):
        return {"constituency": None, "error": "Already voted"}
        
    constituency = get_voter_constituency(voter_id)
    return {"constituency": constituency}

@app.get("/stop_camera")
def stop_camera_endpoint():
    from main import manager
    manager.force_stop()
    return {"status": "camera_stopped"}

@app.get("/all_voters")
def all_voters():
    voters = get_all_voters()
    return voters

@app.get("/age_group_summary")
def age_group_summary():
    return get_age_group_summary()
import bcrypt
import secrets

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/login")
def login(request: LoginRequest):
    # Connect to DB
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT voter_id, password_hash FROM voters WHERE email = %s", (request.email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return {"error": "Invalid credentials"}
    voter_id, pwd_hash = row
    if not bcrypt.checkpw(request.password.encode('utf-8'), pwd_hash.encode('utf-8')):
        return {"error": "Invalid credentials"}
    # Simple token generation (replace with JWT in production)
    token = secrets.token_urlsafe(32)
    return {"token": token, "voter_id": voter_id}

class ForgotPasswordRequest(BaseModel):
    email: str
    dob: str
    new_password: str

@app.post("/forgot_password")
def forgot_password_endpoint(request: ForgotPasswordRequest):
    import os
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Select voter by email
        cur.execute("SELECT voter_id, date_of_birth FROM voters WHERE email = %s", (request.email,))
        row = cur.fetchone()
        
        if not row:
            cur.close()
            conn.close()
            return {"error": "Email address not found in our records."}
            
        voter_id, db_dob = row
        if not db_dob:
            cur.close()
            conn.close()
            return {"error": "Date of Birth records are missing for this voter. Please contact admin."}
            
        # Standardize and compare DOB
        db_dob_str = str(db_dob).strip().replace('-', '/')
        input_dob_str = request.dob.strip().replace('-', '/')
        
        if db_dob_str != input_dob_str:
            cur.close()
            conn.close()
            return {"error": "Incorrect Date of Birth for this email."}
            
        # Hash new password
        pwd_hash = bcrypt.hashpw(request.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password hash in DB
        cur.execute("UPDATE voters SET password_hash = %s WHERE email = %s", (pwd_hash, request.email))
        conn.commit()
        
        cur.close()
        conn.close()
        
        # Also update voter_credentials.txt locally so it matches!
        try:
            cred_file = "voter_credentials.txt"
            if os.path.exists(cred_file):
                with open(cred_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                new_lines = []
                updated = False
                for line in lines:
                    if line.startswith(f"{request.email}:"):
                        new_lines.append(f"{request.email}: {request.new_password}\n")
                        updated = True
                    else:
                        new_lines.append(line)
                if not updated:
                    new_lines.append(f"{request.email}: {request.new_password}\n")
                with open(cred_file, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
        except Exception as file_err:
            print(f"Error updating voter_credentials.txt: {file_err}")
            
        return {"status": "success", "message": "Password reset successfully."}
        
    except Exception as e:
        print(f"Error resetting password: {e}")
        return {"error": "Server error. Please try again."}

@app.get("/voter_activity")
def voter_activity(voter_id: str):
    """Return basic activity info for a voter.
    Includes name, voting status, constituency.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "SELECT full_name, voted, parliamentary_constituency, date_of_birth FROM voters WHERE voter_id = %s",
            (voter_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return {"error": "Voter not found"}
        full_name, voted, constituency, dob = row
        return {
            "voter_id": voter_id,
            "full_name": full_name,
            "voted": voted,
            "constituency": constituency,
            "dob": str(dob) if dob else "N/A"
        }
    except Exception as e:
        print(f"Error fetching voter activity: {e}")
        return {"error": "Server error"}
