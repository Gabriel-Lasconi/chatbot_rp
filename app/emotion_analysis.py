# app/emotion_analysis.py

from transformers import pipeline


class EmotionDetector:
    def __init__(self):
        self.zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

        # candidate emotions taken from the table in literature review
        self.candidate_emotions = [
            "excitement", "anticipation", "anxiety", "curiosity", "eagerness",
            "frustration", "tension", "defensiveness", "conflict", "uncertainty",
            "relief", "trust", "acceptance", "cohesion", "camaraderie", "optimism",
            "confidence", "enthusiasm", "pride", "accomplishment", "satisfaction",
            "nostalgia", "closure", "sadness", "reflection"
        ]

    def detect_emotion(self, text: str):
        """
        Detect emotion using zero-shot classification.

        Args:
            text (str): Input text.

        Returns:
            dict: The dominant emotion, its confidence score, and all emotion scores.
        """
        if not text.strip():
            return {"label": "uncertainty", "score": 1.0, "all_scores": [{"label": "uncertainty", "score": 1.0}]}

        result = self.zero_shot_classifier(text, self.candidate_emotions)

        dominant_emotion = result["labels"][0]
        confidence = result["scores"][0]

        all_scores = [{"label": label, "score": score} for label, score in zip(result["labels"], result["scores"])]

        return {"label": dominant_emotion, "score": confidence, "all_scores": all_scores}
