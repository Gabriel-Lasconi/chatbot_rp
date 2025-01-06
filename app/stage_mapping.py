# stage_mapping.py
from langchain_ollama import OllamaLLM

class StageMapper:
    def __init__(self):
        """
        Maps top-five emotions to Tuckman stages. Also provides short feedback for any stage.
        """
        self.stage_emotion_map = {
            "Forming": ["excitement", "anticipation", "anxiety", "curiosity", "eagerness"],
            "Storming": ["frustration", "tension", "defensiveness", "conflict", "uncertainty"],
            "Norming": ["relief", "trust", "acceptance", "cohesion", "camaraderie", "optimism"],
            "Performing": ["confidence", "enthusiasm", "pride", "accomplishment", "satisfaction"],
            "Adjourning": ["nostalgia", "closure", "sadness", "reflection"]
        }
        self.llama_model = OllamaLLM(model="llama3.2")

    def get_stage_distribution(self, top5_emotions):
        """
        Given the top-five emotions (each a dict with 'label' and 'score'),
        return a dictionary summarizing how much each Tuckman stage is 'activated'.
        For each emotion in the top 5, we add its confidence to whichever stage it belongs to.
        E.g.:
          {
            "Forming": total_conf,
            "Storming": total_conf,
            "Norming": ...
            ...
          }
        """
        # Initialize each stage total to 0
        distribution = {stage: 0.0 for stage in self.stage_emotion_map}

        for emo_dict in top5_emotions:
            emotion_label = emo_dict["label"]
            confidence = emo_dict["score"]  # e.g., 0.2 => 20%
            # Find which stage this emotion belongs to
            stage_for_emo = self._which_stage(emotion_label)
            if stage_for_emo:
                distribution[stage_for_emo] += confidence

        return distribution

    def _which_stage(self, emotion_label):
        """
        Return the stage name that contains the given emotion_label, or None if not found.
        """
        for stage, emos in self.stage_emotion_map.items():
            if emotion_label in emos:
                return stage
        return None

    def get_feedback_for_stage(self, stage: str):
        """
        Generate short feedback for a specific stage using LLaMA.
        """
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
            print(f"[ERROR stage_mapping] {e}")
            return "An error occurred while generating feedback."