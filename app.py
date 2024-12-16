import gradio as gr
from app.chatbot_generative import ChatbotGenerative

# Initialize your chatbot
chatbot = ChatbotGenerative()

def chat_with_bot(user_input):
    """
    Function to interact with the chatbot.
    Args:
        user_input (str): User's message.
    Returns:
        str: Chatbot response.
    """
    result = chatbot.process_message(user_input)
    response = result["bot_message"]
    feedback = result.get("feedback", "")
    stage = result.get("stage", "")

    if feedback:
        return f"Bot: {response}\nFeedback: {feedback}\nStage: {stage}"
    return f"Bot: {response}"

# Gradio Interface
demo = gr.Interface(
    fn=chat_with_bot,
    inputs="text",
    outputs="text",
    title="Team Development Chatbot",
    description="Ask questions about your team's progress and feelings to identify Tuckman's team development stages.",
)

# Launch for local testing
if __name__ == "__main__":
    demo.launch()
