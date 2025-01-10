# main.py

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List

from app.db import init_db, SessionLocal
from sqlalchemy.orm import Session

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

class AnalyzeRequest(BaseModel):
    team_name: str
    lines: List[str]

@app.post("/analyze")
def analyze_conversation(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Endpoint that takes a team_name and a list of lines (strings).
    The chatbot processes each line in 'analysis mode' using the DB-based approach,
    returning the final stage and feedback if found.
    """
    final_stage, feedback = chatbot.analyze_conversation_db(db, req.team_name, req.lines)
    return {
        "final_stage": final_stage if final_stage else "Uncertain",
        "feedback": feedback if feedback else ""
    }

chatbot = ChatbotGenerative()

class Message(BaseModel):
    text: str
    team_name: str

@app.get("/")
def root():
    return {"message": "Chatbot API"}

@app.post("/chat")
def chat_with_bot(message: Message, db: Session = Depends(get_db)):
    """
    Provide a single line of text from a given team to the chatbot.
    The chatbot will load or create the team's state from the database,
    then process the line, updating stage if needed.
    """
    bot_msg, final_stage, feedback = chatbot.process_line(db, message.team_name, message.text)
    return {
        "bot_message": bot_msg,
        "stage": final_stage,
        "feedback": feedback
    }

@app.post("/reset")
def reset_team(message: Message, db: Session = Depends(get_db)):
    """
    Resets the given team's conversation state and messages in the DB.
    """
    chatbot.reset_team(db, message.team_name)
    return {"message": f"Team '{message.team_name}' has been reset."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
