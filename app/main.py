from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from app.chatbot_generative import ChatbotGenerative

# Initialize the FastAPI app
app = FastAPI()

# Allow CORS for all origins (useful during development/testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Chatbot instance in "conversation" mode
chatbot = ChatbotGenerative()


# Pydantic model for the user's input text
class Message(BaseModel):
    text: str


@app.get("/")
def root():
    """
    Root endpoint to check if the API is working.
    """
    return {"message": "Welcome to the Chatbot API (Conversation Mode)!"}


@app.post("/chat")
def chat_with_bot(message: Message):
    """
    Endpoint to have a one-on-one conversation with the chatbot.

    Each POST request sends one user message. The chatbot responds
    with a short answer and possibly partial or final stage feedback
    if it has enough confidence in its classification.
    """
    # We call the "process_line" method (updated in your ChatbotGenerative),
    # which will return (bot_message, final_stage, stage_feedback).
    bot_message, final_stage, feedback = chatbot.process_line(message.text)

    return {
        "bot_message": bot_message,
        "stage": final_stage,
        "feedback": feedback,
    }


@app.post("/reset")
def reset_chat():
    """
    Endpoint to reset the chatbot conversation state,
    clearing all chat history and stage confidence.
    """
    chatbot.reset_conversation()
    return {"message": "Chatbot session has been reset."}


# Run the Uvicorn server with environment variable PORT compatibility
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
