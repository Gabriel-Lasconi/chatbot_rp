# app/chatbot.py

from app.emotion_analysis import EmotionDetector
from app.stage_mapping import StageMapper
from datetime import datetime
import json


class Chatbot:
    def __init__(self, log_file_path="chat_logs.json"):
        self.emotion_detector = EmotionDetector()
        self.stage_mapper = StageMapper()

        # generic questions to start with
        self.questions = [
            "How do you feel about the team's communication?",
            "What do you think about the team's collaboration?",
            "How is the team progressing toward its goals?",
            "Is there any conflict or frustration in the team?",
        ]
        self.current_question = 0
        self.chat_history = []

        self.log_file_path = log_file_path

    def ask_next_question(self):
        """
        Get the next question from the list.
        """
        if self.current_question < len(self.questions):
            question = self.questions[self.current_question]
            self.current_question += 1
            return question
        return None

    def log_interaction(self, user_message, bot_response, emotion_results):
        """
        Logs the user and bot interactions, along with detected emotions, to a JSON file.
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "emotions": emotion_results,
        }
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(interaction) + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to log interaction: {e}")

    def process_message(self, text: str):
        """
        Process the user's response, detect emotions, map to a stage, and generate feedback.
        """
        try:
            # Detect emotions
            emotion_results = self.emotion_detector.detect_emotion(text)
            dominant_emotion = emotion_results["label"]
            confidence = emotion_results["score"]
            print(f"[DEBUG] Dominant emotion: {dominant_emotion} (confidence: {confidence:.2f})")

            # map emotion to stage
            stage = self.stage_mapper.map_emotion_to_stage(dominant_emotion)

            # generate feedback for the stage
            feedback = self.stage_mapper.get_feedback_for_stage(stage)

            # ask next question or provide feedback
            next_question = self.ask_next_question()
            if next_question:
                self.log_interaction(text, next_question, emotion_results["all_scores"])
                return {"bot_message": next_question, "stage": stage, "feedback": feedback}

            self.log_interaction(text, feedback, emotion_results["all_scores"])
            return {"bot_message": feedback, "stage": stage, "feedback": feedback}

        except Exception as e:
            print(f"[ERROR] Exception in process_message: {e}")
            return {"bot_message": "An error occurred. Please try again.", "stage": "Error", "feedback": None}

    def reset_conversation(self):
        """
        Reset the conversation state for a new session.
        """
        self.current_question = 0
        self.chat_history = []

    def get_chat_history(self):
        """
        Retrieve the chat history for the current session.
        """
        return self.chat_history

