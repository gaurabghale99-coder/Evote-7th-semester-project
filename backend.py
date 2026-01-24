from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import recognize_face_once, mark_as_voted

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Face login endpoint
@app.get("/face_login")
def face_login():
    res = recognize_face_once()

    if not res:
        return {"status": "unknown"}

    if res.get("voted") is True:
        return {"status": "already_voted", "name": res.get("name")}

    return {
        "status": "allowed",
        "name": res.get("name"),
        "voter_id": res.get("id"),
        "voter_code": res.get("code")
    }

# Record vote endpoint
class VoteRecord(BaseModel):
    voter_id: int

@app.post("/record_vote")
def record_vote(data: VoteRecord):
    success = mark_as_voted(data.voter_id)
    if success:
        return {"status": "success"}
    return {"status": "failed", "message": "Could not record vote or already voted"}
