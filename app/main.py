# app/main.py

import os
from typing import List, Optional

from fastapi import FastAPI, Depends, Query, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import init_db, SessionLocal, Team, Member, Message
from app.chatbot_generative import ChatbotGenerative

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================
# DATABASE INITIALIZATION
# ========================================================
@app.on_event("startup")
def on_startup():
    init_db()

def get_db():
    """
    Dependency that provides a database session.
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

static_path = os.path.join(os.path.dirname(__file__), "..")
app.mount("/static", StaticFiles(directory=static_path), name="static")

chatbot = ChatbotGenerative()

class AnalyzeRequest(BaseModel):
    team_name: str
    member_name: Optional[str] = None  # Made optional
    lines: List[str]

class ChatRequest(BaseModel):
    text: str
    team_name: str
    member_name: str

# ========================================================
# ROUTES
# ========================================================

@app.get("/", response_class=HTMLResponse)
def root_page():
    """
    Serves the main HTML page.
    """
    index_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)

@app.get("/teaminfo")
def get_team_info(team_name: str = Query(...), db: Session = Depends(get_db)):
    """
    Retrieves team information, including stage distribution and feedback.

    Args:
        team_name (str): The name of the team.
        db (Session): Database session.

    Returns:
        dict: Contains distribution, final_stage, and feedback.
    """
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team:
        team = Team(name=team_name, current_stage="Uncertain", feedback="")
        db.add(team)
        db.commit()
        db.refresh(team)
        return {"distribution": {}, "final_stage": "Uncertain", "feedback": ""}

    distribution = team.load_team_distribution()
    final_stage = team.current_stage
    feedback = team.feedback if team.feedback else ""

    return {
        "distribution": distribution,
        "final_stage": final_stage,
        "feedback": feedback
    }

@app.get("/memberinfo")
def get_member_info(team_name: str = Query(...), member_name: str = Query(...), db: Session = Depends(get_db)):
    """
    Retrieves member information, including stage distribution and personal feedback.

    Args:
        team_name (str): The name of the team.
        member_name (str): The name of the member.
        db (Session): Database session.

    Returns:
        dict: Contains distribution, final_stage, accum_emotions, and personal_feedback.
    """
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")

    member = db.query(Member).filter(
        Member.team_id == team.id,
        Member.name == member_name
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this team.")

    personal_dist = member.load_accum_distrib()
    personal_stage = member.current_stage
    personal_emotions = member.load_accum_emotions()
    personal_feedback = member.personal_feedback if member.personal_feedback else ""

    return {
        "distribution": personal_dist,
        "final_stage": personal_stage,
        "accum_emotions": personal_emotions,
        "personal_feedback": personal_feedback
    }

@app.post("/chat")
def chat_with_bot(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Handles chat messages sent by users in Conversation Mode.

    Args:
        req (ChatRequest): The chat request containing text, team_name, and member_name.
        db (Session): Database session.

    Returns:
        dict: Contains bot_message, stage information, and emotions data.
    """
    bot_msg, final_stage, feedback, accum_dist, last_emotion_dist, accum_emotions, personal_feedback = chatbot.process_line(
        db, req.team_name, req.member_name, req.text
    )

    the_team = db.query(Team).filter(Team.name == req.team_name).first()
    team_distribution = the_team.load_team_distribution()
    team_feedback = the_team.feedback

    return {
        "bot_message": bot_msg,
        "stage": final_stage if final_stage else "Uncertain",
        "feedback": feedback if feedback else "No feedback available.",
        "distribution": team_distribution,
        "team_feedback": team_feedback if team_feedback else "No team feedback available.",
        "my_stage_feedback": personal_feedback if personal_feedback else "No personal feedback available.",
        "last_emotion_dist": last_emotion_dist,
        "accum_emotions": accum_emotions
    }

@app.post("/analyze")
def analyze_conversation(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Analyzes a bulk conversation input in Analysis Mode.

    Args:
        req (AnalyzeRequest): The analysis request containing team_name, member_name, and lines of conversation.
        db (Session): Database session.

    Returns:
        dict: Contains final_stage, feedback, distribution, and team_feedback.
    """
    try:
        final_stage, feedback, _ = chatbot.analyze_conversation_db(
            db, req.team_name, req.lines
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing conversation: {str(e)}")

    the_team = db.query(Team).filter(Team.name == req.team_name).first()
    if not the_team:
        raise HTTPException(status_code=404, detail="Team not found.")

    team_distribution = the_team.load_team_distribution()
    team_feedback = the_team.feedback if the_team.feedback else ""

    return {
        "final_stage": final_stage if final_stage else "Uncertain",
        "feedback": feedback if feedback else "",
        "distribution": team_distribution,
        "team_feedback": team_feedback
    }

@app.post("/analyze-file")
async def analyze_file(
    team_name: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Analyzes a chat log file uploaded by the user.

    Args:
        team_name (str): The name of the team.
        file (UploadFile): The uploaded text file containing the chat log.
        db (Session): Database session.

    Returns:
        dict: Contains final_stage, feedback, and distribution.
    """
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    try:
        file_contents = (await file.read()).decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read the uploaded file.")

    lines = file_contents.splitlines()

    try:
        final_stage, feedback, distribution = chatbot.analyze_conversation_db(
            db, team_name, lines
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing conversation: {str(e)}")

    return {
        "final_stage": final_stage,
        "feedback": feedback,
        "distribution": distribution
    }

@app.post("/reset")
def reset_team(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Resets a team's stage and clears all associated member data.

    Args:
        req (ChatRequest): The reset request containing team_name.
        db (Session): Database session.

    Returns:
        dict: Confirmation message about the reset action.
    """
    team = db.query(Team).filter(Team.name == req.team_name).first()
    if team:
        team.current_stage = "Uncertain"
        team.feedback = ""  # Clear team feedback
        for member in team.members:
            member.current_stage = "Uncertain"
            member.save_accum_distrib({})
            member.num_lines = 0
            member.save_accum_emotions({})
            member.personal_feedback = ""  # Clear personal feedback
            db.query(Message).filter(Message.member_id == member.id).delete()
            db.commit()
        db.commit()

    return {"message": f"Team '{req.team_name}' has been reset."}

# ========================================================
# MAIN APPLICATION
# ========================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
