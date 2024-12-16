# app/main.py - class for starting the uvicorn server

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# from app.chatbot import Chatbot
from app.chatbot_generative import ChatbotGenerative

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],)

chatbot = ChatbotGenerative()

class Message(BaseModel):
    text: str
@app.get("/")
def root():
    return {"message": "Welcome to the Chatbot API!"}
@app.post("/chat")
def chat_with_bot(message: Message):
    """
    Endpoint to interact with the chatbot.
    """
    result = chatbot.process_message(message.text)
    return {"bot_message": result["bot_message"], "stage": result["stage"], "feedback": result["feedback"]}
@app.post("/reset")
def reset_chat():
    chatbot.reset_conversation()
    return {"message": "Chatbot session has been reset."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
