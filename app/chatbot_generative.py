# from langchain_ollama import OllamaLLM
# from app.emotion_analysis import EmotionDetector
# from app.stage_mapping import StageMapper
#
#
# class ChatbotGenerative:
#     def __init__(self):
#         """
#         Initializes the chatbot using the Ollama LLaMA model.
#         """
#         # Load the LLaMA model via Ollama
#         self.model = OllamaLLM(model="llama3.2")
#
#         # Initialize emotion detector and stage mapper
#         self.emotion_detector = EmotionDetector()
#         self.stage_mapper = StageMapper()
#
#         # Conversation state
#         self.chat_history = []
#         self.questions_asked = 0
#         self.max_questions = 3
#
#         # System instructions
#         self.system_instructions = (
#             "You are a helpful assistant that identifies a team's emotional climate "
#             "and maps it to Tuckman's stages of team development. Over the course of up to 3 user responses, "
#             "ask natural and brief follow-up questions about the team's feelings, then provide concluding feedback."
#         )
#
#     def build_prompt(self, user_message):
#         """
#         Build the prompt for the LLaMA model including system instructions and chat history.
#         """
#         # Combine system instructions and conversation history
#         conversation_str = "\n".join(self.chat_history)
#
#         # Add the user message
#         prompt = (
#             f"<<SYS>>\n{self.system_instructions}\n<</SYS>>\n\n"
#             f"{conversation_str}\n"
#             f"User: {user_message}\n"
#             "Assistant:"
#         )
#         return prompt
#
#     def generate_response(self, user_message):
#         """
#         Generate a response using the LLaMA model via Ollama.
#         """
#         prompt = self.build_prompt(user_message)
#
#         # Invoke the LLaMA model for generating the response
#         response = self.model.invoke(input=prompt)
#
#         # Clean and process the response
#         assistant_response = response.strip()
#
#         # Update chat history
#         self.chat_history.append(f"User: {user_message}")
#         self.chat_history.append(f"Assistant: {assistant_response}")
#
#         return assistant_response
#
#     def process_message(self, text):
#         """
#         Process the user's message, detect emotions, map to a stage, and generate a response.
#         """
#         try:
#             # Detect emotions
#             emotion_results = self.emotion_detector.detect_emotion(text)
#             dominant_emotion = emotion_results["label"]
#
#             # Map emotion to stage and provide feedback
#             stage = self.stage_mapper.map_emotion_to_stage(dominant_emotion)
#             feedback = self.stage_mapper.get_feedback_for_stage(stage)
#
#             self.questions_asked += 1
#
#             if self.questions_asked < self.max_questions:
#                 bot_response = self.generate_response(text)
#                 return {"bot_message": bot_response, "stage": None, "feedback": None}
#             else:
#                 bot_response = self.generate_response(text)
#                 return {"bot_message": bot_response, "stage": stage, "feedback": feedback}
#
#         except Exception as e:
#             print(f"[ERROR] {e}")
#             return {"bot_message": "An error occurred. Please try again.", "stage": "Error", "feedback": None}
#
#     def reset_conversation(self):
#         """
#         Reset the conversation state for a new session.
#         """
#         self.questions_asked = 0
#         self.chat_history = []
#
#
# if __name__ == "__main__":
#     chatbot = ChatbotGenerative()
#     print("Chatbot is ready! Type 'reset' to reset the conversation or 'exit' to quit.")
#
#     while True:
#         user_input = input("You: ")
#         if user_input.lower() == "exit":
#             print("Goodbye!")
#             break
#         elif user_input.lower() == "reset":
#             chatbot.reset_conversation()
#             print("Conversation reset.")
#         else:
#             result = chatbot.process_message(user_input)
#             print("Bot:", result["bot_message"])
#             if result["feedback"]:
#                 print("Bot (Stage Feedback):", result["feedback"])

# chatbot_generative.py (Updated)
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

        # We'll store the "current_stage" and a confidence measure for it
        self.current_stage = None
        self.stage_confidence = 0
        self.stage_confidence_threshold = 3  # for example, require 3 consistent lines to finalize

        # System instructions: keep responses short, ask relevant follow-ups
        self.system_instructions = (
            "You are a concise assistant analyzing a team's emotional climate "
            "and mapping it to Tuckman's stages. Only ask short follow-up questions "
            "until you feel confident about the team's stage. Provide short concluding feedback. "
            "Avoid lengthy elaborations or repeating instructions. "
        )

    def build_prompt(self, user_message):
        """
        Build the prompt for the LLaMA model including system instructions and chat history.
        """
        conversation_str = "\n".join(self.chat_history)
        prompt = (
            f"<<SYS>>\n{self.system_instructions}\n<</SYS>>\n\n"
            f"{conversation_str}\n"
            f"User: {user_message}\n"
            "Assistant:"
        )
        return prompt

    def generate_response(self, user_message):
        """
        Generate a concise response using the LLaMA model via Ollama.
        """
        prompt = self.build_prompt(user_message)
        response = self.model.invoke(input=prompt)
        assistant_response = response.strip()

        # Append to history
        self.chat_history.append(f"User: {user_message}")
        self.chat_history.append(f"Assistant: {assistant_response}")

        return assistant_response

    def process_line(self, text):
        """
        Process a single line from the user or script, detect emotion, update stage confidence,
        and generate a short response. Returns (bot_message, final_stage, stage_feedback).
        """
        # 1. Detect emotion
        emotion_results = self.emotion_detector.detect_emotion(text)
        dominant_emotion = emotion_results["label"]

        # 2. Map to stage (with memory logic inside stage mapper)
        new_stage = self.stage_mapper.infer_stage_with_memory(dominant_emotion, self.current_stage)

        # If stage changed, reset or upgrade confidence
        if new_stage != self.current_stage:
            self.current_stage = new_stage
            self.stage_confidence = 1 if new_stage != "Uncertain" else 0
        else:
            # If the stage remains the same and isn't "Uncertain", increment confidence
            if self.current_stage != "Uncertain":
                self.stage_confidence += 1

        # 3. Generate short response from the LLaMA model
        bot_response = self.generate_response(text)

        # 4. If the stage_confidence exceeds threshold, we can produce concluding feedback
        if self.current_stage != "Uncertain" and self.stage_confidence >= self.stage_confidence_threshold:
            stage_feedback = self.stage_mapper.get_feedback_for_stage(self.current_stage)
            return bot_response, self.current_stage, stage_feedback
        else:
            return bot_response, None, None

    def interactive_chat(self):
        """
        Holds a conversation with a person line by line,
        continuing until the user says 'exit' or we reach stage confidence.
        """
        print("Chatbot is ready! Type 'exit' to quit. We'll keep going until we confirm a stage or you stop.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            bot_msg, final_stage, feedback = self.process_line(user_input)
            print("Bot:", bot_msg)
            if final_stage:
                print(f"[Stage Conclusion: {final_stage}]")
                print("Bot (Stage Feedback):", feedback)
                # After concluding, you could break or let the user continue
                # but typically you'd break since we have a conclusion
                break

    def analyze_conversation(self, lines):
        """
        Analyzes a list of lines (strings) as if they're a conversation.
        Returns the final stage and stage feedback once confident or end of lines.
        """
        final_stage = None
        feedback = None
        for line in lines:
            bot_msg, concluded_stage, concluded_feedback = self.process_line(line)
            # We won't do line-by-line prints here, but you can log them if you want
            if concluded_stage:
                final_stage = concluded_stage
                feedback = concluded_feedback
                break  # We can stop analyzing once we have confidence
        return final_stage, feedback

    def reset_conversation(self):
        """
        Reset the conversation state for a new session or new analysis.
        """
        self.chat_history = []
        self.current_stage = None
        self.stage_confidence = 0

