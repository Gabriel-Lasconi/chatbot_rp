from langchain_ollama import OllamaLLM
from app.emotion_analysis import EmotionDetector
from app.stage_mapping import StageMapper


class ChatbotGenerative:
    def __init__(self):
        """
        Initializes the chatbot using the Ollama LLaMA model.
        """
        # Load the LLaMA model via Ollama
        self.model = OllamaLLM(model="llama3.2")

        # Initialize emotion detector and stage mapper
        self.emotion_detector = EmotionDetector()
        self.stage_mapper = StageMapper()

        # Conversation state
        self.chat_history = []
        self.questions_asked = 0
        self.max_questions = 3

        # System instructions
        self.system_instructions = (
            "You are a helpful assistant that identifies a team's emotional climate "
            "and maps it to Tuckman's stages of team development. Over the course of up to 3 user responses, "
            "ask natural and brief follow-up questions about the team's feelings, then provide concluding feedback."
        )

    def build_prompt(self, user_message):
        """
        Build the prompt for the LLaMA model including system instructions and chat history.
        """
        # Combine system instructions and conversation history
        conversation_str = "\n".join(self.chat_history)

        # Add the user message
        prompt = (
            f"<<SYS>>\n{self.system_instructions}\n<</SYS>>\n\n"
            f"{conversation_str}\n"
            f"User: {user_message}\n"
            "Assistant:"
        )
        return prompt

    def generate_response(self, user_message):
        """
        Generate a response using the LLaMA model via Ollama.
        """
        prompt = self.build_prompt(user_message)

        # Invoke the LLaMA model for generating the response
        response = self.model.invoke(input=prompt)

        # Clean and process the response
        assistant_response = response.strip()

        # Update chat history
        self.chat_history.append(f"User: {user_message}")
        self.chat_history.append(f"Assistant: {assistant_response}")

        return assistant_response

    def process_message(self, text):
        """
        Process the user's message, detect emotions, map to a stage, and generate a response.
        """
        try:
            # Detect emotions
            emotion_results = self.emotion_detector.detect_emotion(text)
            dominant_emotion = emotion_results["label"]

            # Map emotion to stage and provide feedback
            stage = self.stage_mapper.map_emotion_to_stage(dominant_emotion)
            feedback = self.stage_mapper.get_feedback_for_stage(stage)

            self.questions_asked += 1

            if self.questions_asked < self.max_questions:
                bot_response = self.generate_response(text)
                return {"bot_message": bot_response, "stage": None, "feedback": None}
            else:
                bot_response = self.generate_response(text)
                return {"bot_message": bot_response, "stage": stage, "feedback": feedback}

        except Exception as e:
            print(f"[ERROR] {e}")
            return {"bot_message": "An error occurred. Please try again.", "stage": "Error", "feedback": None}

    def reset_conversation(self):
        """
        Reset the conversation state for a new session.
        """
        self.questions_asked = 0
        self.chat_history = []


if __name__ == "__main__":
    chatbot = ChatbotGenerative()
    print("Chatbot is ready! Type 'reset' to reset the conversation or 'exit' to quit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        elif user_input.lower() == "reset":
            chatbot.reset_conversation()
            print("Conversation reset.")
        else:
            result = chatbot.process_message(user_input)
            print("Bot:", result["bot_message"])
            if result["feedback"]:
                print("Bot (Stage Feedback):", result["feedback"])
