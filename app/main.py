from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from app.chatbot_generative import ChatbotGenerative

# Initialize the FastAPI app
app = FastAPI()

# Allow CORS for all origins during development/testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Chatbot instance
chatbot = ChatbotGenerative()

# Pydantic model for message input
class Message(BaseModel):
    text: str

@app.get("/")
def root():
    """
    Root endpoint to check if the API is working.
    """
    return {"message": "Welcome to the Chatbot API!"}

@app.post("/chat")
def chat_with_bot(message: Message):
    """
    Endpoint to interact with the chatbot.
    """
    result = chatbot.process_message(message.text)
    return {
        "bot_message": result["bot_message"],
        "stage": result["stage"],
        "feedback": result["feedback"],
    }

@app.post("/reset")
def reset_chat():
    """
    Endpoint to reset the chatbot conversation.
    """
    chatbot.reset_conversation()
    return {"message": "Chatbot session has been reset."}

# Run the Uvicorn server with Render compatibility
if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment variable if it exists, otherwise default to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
