# from langchain_ollama import OllamaLLM
#
# class StageMapper:
#     def __init__(self):
#         self.stage_emotion_map = {
#             "Forming": ["excitement", "anticipation", "anxiety", "curiosity", "eagerness"],
#             "Storming": ["frustration", "tension", "defensiveness", "conflict", "uncertainty"],
#             "Norming": ["relief", "trust", "acceptance", "cohesion", "camaraderie", "optimism"],
#             "Performing": ["confidence", "enthusiasm", "pride", "accomplishment", "satisfaction"],
#             "Adjourning": ["nostalgia", "closure", "sadness", "reflection"]
#         }
#
#         # LLaMA model for generating dynamic feedback
#         self.llama_model = OllamaLLM(model="llama3.2")
#
#     def map_emotion_to_stage(self, emotions_with_confidences):
#         """
#         Map multiple emotions with confidence levels to the most likely stage.
#
#         Args:
#             emotions_with_confidences (list of tuples): List of (emotion, confidence).
#
#         Returns:
#             str: The most probable stage based on cumulative confidence.
#         """
#         if not emotions_with_confidences or not isinstance(emotions_with_confidences, list):
#             return "Uncertain"
#
#         # Initialize cumulative confidence scores for each stage
#         stage_confidences = {stage: 0 for stage in self.stage_emotion_map}
#
#         # Aggregate confidence scores for each stage
#         for emotion, confidence in emotions_with_confidences:
#             for stage, emotions in self.stage_emotion_map.items():
#                 if emotion in emotions:
#                     stage_confidences[stage] += confidence
#
#         # Find the stage with the highest cumulative confidence
#         best_stage = max(stage_confidences, key=stage_confidences.get)
#
#         # Return "Uncertain" if all confidence scores are zero
#         if stage_confidences[best_stage] == 0:
#             return "Uncertain"
#
#         return best_stage
#
#     def get_feedback_for_stage(self, stage: str):
#         """
#         Generate dynamic feedback for a specific team stage using LLaMA.
#
#         Args:
#             stage (str): Team stage.
#
#         Returns:
#             str: Dynamically generated feedback for the stage.
#         """
#         if stage not in self.stage_emotion_map:
#             return "No feedback available for this stage."
#
#         # Build prompt for LLaMA
#         prompt = (
#             f"You are a team dynamics expert. Provide thoughtful and practical advice for a team in the '{stage}' stage "
#             f"of Tuckman's model of team development. Include actionable suggestions to improve team performance and to handle this stage better."
#             f"Please keep the message brief (around 2-3 sentences) and use basic english. "
#             f"Do not write the message in bullet points or ordered lists. Write it as a normal message."
#         )
#
#         try:
#             # Invoke LLaMA to generate feedback
#             response = self.llama_model.invoke(input=prompt)
#             return response.strip()
#         except Exception as e:
#             print(f"[ERROR] Failed to generate feedback with LLaMA: {e}")
#             return "An error occurred while generating feedback. Please try again."

# stage_mapping.py (updated snippet)
from langchain_ollama import OllamaLLM

class StageMapper:
    def __init__(self):
        self.stage_emotion_map = {
            "Forming": ["excitement", "anticipation", "anxiety", "curiosity", "eagerness"],
            "Storming": ["frustration", "tension", "defensiveness", "conflict", "uncertainty"],
            "Norming": ["relief", "trust", "acceptance", "cohesion", "camaraderie", "optimism"],
            "Performing": ["confidence", "enthusiasm", "pride", "accomplishment", "satisfaction"],
            "Adjourning": ["nostalgia", "closure", "sadness", "reflection"]
        }
        self.llama_model = OllamaLLM(model="llama3.2")
        self.stage_order = ["Forming", "Storming", "Norming", "Performing", "Adjourning"]

    def infer_stage_with_memory(self, emotion_label, current_stage):
        # Direct single-label stage
        new_stage = self.map_emotion_to_single(emotion_label)
        if new_stage == "Uncertain":
            return current_stage or "Uncertain"

        if current_stage and current_stage != "Uncertain":
            # Only "upgrade" if new_stage is beyond the old stage
            if self.is_stage_higher(new_stage, current_stage):
                return new_stage
            else:
                return current_stage
        else:
            return new_stage

    def map_emotion_to_single(self, emotion_label):
        for stage, emos in self.stage_emotion_map.items():
            if emotion_label in emos:
                return stage
        return "Uncertain"

    def is_stage_higher(self, new_stage, old_stage):
        return self.stage_order.index(new_stage) > self.stage_order.index(old_stage)

    def get_feedback_for_stage(self, stage: str):
        if stage not in self.stage_emotion_map:
            return "No feedback available for this stage."

        prompt = (
            f"You are a helpful assistant. Give a SHORT 2-sentence advice for a team in '{stage}' stage. "
            "Use simple language. Avoid bullet points."
        )
        try:
            response = self.llama_model.invoke(input=prompt)
            return response.strip()
        except Exception as e:
            print(f"[ERROR] {e}")
            return "An error occurred while generating feedback."
