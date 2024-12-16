import gradio as gr
from app.chatbot_generative import ChatbotGenerative

# Initialize the chatbot
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

    # Format the response
    if feedback:
        return f"Bot: {response}\nFeedback: {feedback}\nStage: {stage}"
    return f"Bot: {response}"

demo = gr.Interface(
    fn=chat_with_bot,
    inputs=gr.Textbox(placeholder="Type your message here...", label="User Input"),
    outputs=gr.Textbox(label="Chatbot Response"),
    title="Team Development Chatbot",
    description=(
        "This chatbot helps assess your team's emotional climate and identifies Tuckman's team development stages. "
        "Ask questions and explore insights!"
    ),
)

if __name__ == "__main__":
    demo.launch()