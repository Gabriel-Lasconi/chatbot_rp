# main.py

import os
from typing import List, Optional

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import init_db, SessionLocal
from app.chatbot_generative import ChatbotGenerative
from app.db import Team

app = FastAPI()

# CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mount static folder for styles.css, app.js, etc.
static_path = os.path.join(os.path.dirname(__file__), "..")
app.mount("/static", StaticFiles(directory=static_path), name="static")

chatbot = ChatbotGenerative()

class AnalyzeRequest(BaseModel):
    team_name: str
    lines: List[str]

class Message(BaseModel):
    text: str
    team_name: str

@app.get("/", response_class=HTMLResponse)
def root_page():
    """
    Serve index.html
    """
    index_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "index.html"
    )
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)

@app.get("/teaminfo")
def get_team_info(team_name: str = Query(...), db: Session = Depends(get_db)):
    """
    Returns the current distribution of each stage (Forming, Storming, Norming, Performing, Adjourning)
    and the team's final stage (if any) with feedback, if the stage is not Uncertain.
    If the team doesn't exist, create it with 0 distribution.
    """
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team:
        # Create a new team, distribution 0, stage=Uncertain
        team = Team(name=team_name, current_stage="Uncertain", stage_confidence=0.0)
        db.add(team)
        db.commit()
        db.refresh(team)

    # Load distribution
    accum_dist = team.load_accum_distrib()
    # If brand new, might be {}
    if not accum_dist:
        # Make sure we have 5 keys with 0.0
        accum_dist = {stg: 0.0 for stg in chatbot.stage_mapper.stage_emotion_map.keys()}

    final_stage = team.current_stage
    feedback = ""
    if final_stage and final_stage != "Uncertain":
        feedback = chatbot.stage_mapper.get_feedback_for_stage(final_stage)

    return {
        "distribution": accum_dist,
        "final_stage": final_stage,
        "feedback": feedback
    }

@app.post("/chat")
def chat_with_bot(message: Message, db: Session = Depends(get_db)):
    """
    Single line conversation. Returns the updated distribution, final stage, and feedback if any.
    """
    bot_msg, final_stage, feedback, accum_dist = chatbot.process_line(db, message.team_name, message.text)

    return {
        "bot_message": bot_msg,
        "stage": final_stage if final_stage else "Uncertain",
        "feedback": feedback if feedback else "",
        "distribution": accum_dist
    }

@app.post("/analyze")
def analyze_conversation(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Multi-line conversation analysis. Returns final stage, feedback, distribution, etc.
    """
    final_stage, feedback, accum_dist = chatbot.analyze_conversation_db(db, req.team_name, req.lines)

    return {
        "final_stage": final_stage if final_stage else "Uncertain",
        "feedback": feedback if feedback else "",
        "distribution": accum_dist
    }

@app.post("/reset")
def reset_team(message: Message, db: Session = Depends(get_db)):
    """
    Reset a team's conversation state in the DB.
    """
    chatbot.reset_team(db, message.team_name)
    return {"message": f"Team '{message.team_name}' has been reset."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
