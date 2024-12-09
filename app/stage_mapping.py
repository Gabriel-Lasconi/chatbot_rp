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

        # LLaMA model for generating dynamic feedback
        self.llama_model = OllamaLLM(model="llama3.2")

    def map_emotion_to_stage(self, emotion: str):
        """
        Map an emotion to its corresponding stage.

        Args:
            emotion (str): Detected emotion.

        Returns:
            str: The corresponding stage.
        """
        for stage, emotions in self.stage_emotion_map.items():
            if emotion in emotions:
                return stage
        return "Uncertain"

    def get_feedback_for_stage(self, stage: str):
        """
        Generate dynamic feedback for a specific team stage using LLaMA.

        Args:
            stage (str): Team stage.

        Returns:
            str: Dynamically generated feedback for the stage.
        """
        if stage not in self.stage_emotion_map:
            return "No feedback available for this stage."

        # Build prompt for LLaMA
        prompt = (
            f"You are a team dynamics expert. Provide thoughtful and practical advice for a team in the '{stage}' stage "
            f"of Tuckman's model of team development. Include actionable suggestions to improve team performance and to handle this stage better."
            f"Please keep the message brief (around 2-3 sentences) and use basic english. "
            f"Do not write the message in bullet points or ordered lists. Write it as a normal message"
        )

        try:
            # Invoke LLaMA to generate feedback
            response = self.llama_model.invoke(input=prompt)
            return response.strip()
        except Exception as e:
            print(f"[ERROR] Failed to generate feedback with LLaMA: {e}")
            return "An error occurred while generating feedback. Please try again."
