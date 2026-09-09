import uuid
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from database import db

router = APIRouter(prefix="/chat", tags=["Welele Chat & Reactions"])

class PostCommentRequest(BaseModel):
    episode_id: Optional[str] = None
    user_name: str
    avatar: Optional[str] = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80"
    text: str

class SendReactionRequest(BaseModel):
    episode_id: Optional[str] = None
    emoji: str
    timestamp_seconds: int

@router.get("/episodes/{episode_id}/comments")
def get_comments(episode_id: str):
    comments = db.get("comments")
    episode_comments = [c for c in comments if c.get("episode_id") == episode_id]
    return {"comments": episode_comments, "total": len(episode_comments)}

@router.post("/episodes/{episode_id}/comments")
def post_comment(episode_id: str, req: PostCommentRequest):
    new_comment = {
        "id": f"c_{uuid.uuid4().hex[:8]}",
        "episode_id": episode_id,
        "user_name": req.user_name,
        "avatar": req.avatar,
        "text": req.text,
        "likes": 0,
        "time_ago": "Just now"
    }
    db.insert("comments", new_comment)
    return {"success": True, "comment": new_comment}

@router.get("/episodes/{episode_id}/reactions")
def get_reactions(episode_id: str):
    reactions = db.get("reactions")
    ep_reactions = [r for r in reactions if r.get("episode_id") == episode_id]
    return {"reactions": ep_reactions}

@router.post("/episodes/{episode_id}/reactions")
def send_reaction(episode_id: str, req: SendReactionRequest):
    new_reaction = {
        "id": f"r_{uuid.uuid4().hex[:8]}",
        "episode_id": episode_id,
        "emoji": req.emoji,
        "timestamp_seconds": req.timestamp_seconds
    }
    db.insert("reactions", new_reaction)
    return {"success": True, "reaction": new_reaction}
