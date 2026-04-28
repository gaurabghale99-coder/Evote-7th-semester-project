from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
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
    success = mark_as_voted(data.voter_id)
    if success:
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




