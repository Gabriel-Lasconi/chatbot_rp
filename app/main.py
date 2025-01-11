# main.py

import os
from typing import List

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import init_db, SessionLocal
from app.chatbot_generative import ChatbotGenerative

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB at startup
@app.on_event("startup")
def on_startup():
    init_db()

# Provide a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

static_path = os.path.join(os.path.dirname(__file__), "..")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Chatbot instance
chatbot = ChatbotGenerative()

# Models
class AnalyzeRequest(BaseModel):
    team_name: str
    lines: List[str]

class Message(BaseModel):
    text: str
    team_name: str

@app.get("/", response_class=HTMLResponse)
def root_page():
    """
    Serves the front-end page (index.html) at the root endpoint.
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

@app.post("/analyze")
def analyze_conversation(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Endpoint that processes multiple lines in 'analysis mode'.
    """
    final_stage, feedback = chatbot.analyze_conversation_db(db, req.team_name, req.lines)
    return {
        "final_stage": final_stage if final_stage else "Uncertain",
        "feedback": feedback if feedback else ""
    }

@app.post("/chat")
def chat_with_bot(message: Message, db: Session = Depends(get_db)):
    """
    Endpoint for single-line conversation with the chatbot.
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
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
