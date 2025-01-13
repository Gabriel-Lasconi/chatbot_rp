# main.py

import os
from typing import List

from fastapi import FastAPI, Depends, Query, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import init_db, SessionLocal, Team
from app.chatbot_generative import ChatbotGenerative

app = FastAPI()

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

static_path = os.path.join(os.path.dirname(__file__), "..")
app.mount("/static", StaticFiles(directory=static_path), name="static")

chatbot = ChatbotGenerative()

class AnalyzeRequest(BaseModel):
    team_name: str
    member_name: str
    lines: List[str]

class ChatRequest(BaseModel):
    text: str
    team_name: str
    member_name: str

@app.get("/", response_class=HTMLResponse)
def root_page():
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
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team:
        team = Team(name=team_name, current_stage="Uncertain")
        db.add(team)
        db.commit()
        db.refresh(team)
        return {
            "distribution": {},
            "final_stage": "Uncertain",
            "feedback": ""
        }

    distribution = team.load_team_distribution()
    final_stage = team.current_stage

    feedback = ""
    if final_stage and final_stage != "Uncertain":
        feedback = chatbot.stage_mapper.get_feedback_for_stage(final_stage)

    return {
        "distribution": distribution,
        "final_stage": final_stage,
        "feedback": feedback
    }

@app.post("/chat")
def chat_with_bot(req: ChatRequest, db: Session = Depends(get_db)):
    bot_msg, final_stage, feedback, member_dist, last_emotion_dist = chatbot.process_line(
        db, req.team_name, req.member_name, req.text
    )

    the_team = db.query(Team).filter(Team.name == req.team_name).first()
    team_distribution = the_team.load_team_distribution()

    return {
        "bot_message": bot_msg,
        "stage": final_stage if final_stage else "Uncertain",
        "feedback": feedback if feedback else "",
        "distribution": team_distribution,
        "last_emotion_dist": last_emotion_dist  # <--- we pass the last msg's emotions to front-end
    }

@app.post("/analyze")
def analyze_conversation(req: AnalyzeRequest, db: Session = Depends(get_db)):
    final_stage, feedback, _ = chatbot.analyze_conversation_db(
        db, req.team_name, req.member_name, req.lines
    )

    the_team = db.query(Team).filter(Team.name == req.team_name).first()
    team_distribution = the_team.load_team_distribution()

    return {
        "final_stage": final_stage if final_stage else "Uncertain",
        "feedback": feedback if feedback else "",
        "distribution": team_distribution
    }

@app.post("/analyze-file")
async def analyze_file(
    team_name: str,
    member_name: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    file_contents = (await file.read()).decode("utf-8")
    lines = file_contents.splitlines()

    final_stage, feedback, distribution = chatbot.analyze_conversation_db(
        db, team_name, member_name, lines
    )

    return {
        "final_stage": final_stage,
        "feedback": feedback,
        "distribution": distribution
    }

@app.post("/reset")
def reset_team(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Reset a team's conversation state in the DB.
    (Also resets members' states and messages.)
    """
    chatbot.reset_team(db, req.team_name)
    return {"message": f"Team '{req.team_name}' has been reset."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
