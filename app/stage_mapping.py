# stage_mapping.py

from langchain_ollama import OllamaLLM

class StageMapper:
    def __init__(self):
        """
        Maps emotions to Tuckman stages. Also provides short feedback for any stage.
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
        (Unchanged) Given top-5 emotions from a single message,
        returns how much each Tuckman stage is 'activated.'
        """
        distribution = {stage: 0.0 for stage in self.stage_emotion_map}

        for emo_dict in top5_emotions:
            emotion_label = emo_dict["label"]
            confidence = emo_dict["score"]
            stage_for_emo = self._which_stage(emotion_label)
            if stage_for_emo:
                distribution[stage_for_emo] += confidence

        total_sum = sum(distribution.values())
        if total_sum > 0:
            for stg in distribution:
                distribution[stg] /= total_sum

        return distribution

    def get_stage_distribution_from_entire_emotions(self, accum_emotions):
        """
        NEW METHOD:
        Given a dict of all the member's emotions (e.g. accum_emotions)
        -> { "confidence": 0.3, "sadness": 0.2, ... },
        sum them by Tuckman stage, then normalize.
        """
        distribution = {stage: 0.0 for stage in self.stage_emotion_map}

        # For each emotion in accum_emotions:
        # figure out which stage it belongs to, add its value
        for emotion_label, value in accum_emotions.items():
            stage_for_emo = self._which_stage(emotion_label)
            if stage_for_emo:
                distribution[stage_for_emo] += value

        # Now normalize
        total_sum = sum(distribution.values())
        if total_sum > 0:
            for stg in distribution:
                distribution[stg] /= total_sum

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
        (Unchanged) Generate short feedback for a specific stage using LLaMA.
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
