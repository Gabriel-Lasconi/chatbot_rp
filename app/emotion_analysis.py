from transformers import pipeline


class EmotionDetector:
    def __init__(self):
        self.zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

        # Candidate emotions taken from the table in literature review
        self.candidate_emotions = [
            "excitement", "anticipation", "anxiety", "curiosity", "eagerness",
            "frustration", "tension", "defensiveness", "conflict", "uncertainty",
            "relief", "trust", "acceptance", "cohesion", "camaraderie", "optimism",
            "confidence", "enthusiasm", "pride", "accomplishment", "satisfaction",
            "nostalgia", "closure", "sadness", "reflection"
        ]

    def detect_emotion(self, text: str, top_n: int = 5):
        """
        Detect top emotions using zero-shot classification.

        Args:
            text (str): Input text.
            top_n (int): Number of top emotions to return.

        Returns:
            dict: The dominant emotion, its confidence score, and the top 'n' emotions with confidence scores.
        """
        if not text.strip():
            return {
                "label": "uncertainty",
                "score": 1.0,
                "top_emotions": [{"label": "uncertainty", "score": 1.0}]
            }

        # Perform zero-shot classification
        result = self.zero_shot_classifier(text, self.candidate_emotions)

        # Extract the top N emotions with confidence scores
        top_emotions = [{"label": label, "score": score} for label, score in zip(result["labels"], result["scores"])]
        top_emotions = top_emotions[:top_n]  # Keep only the top N emotions

        # The dominant emotion is the first in the sorted results
        dominant_emotion = top_emotions[0]["label"]
        confidence = top_emotions[0]["score"]

        return {"label": dominant_emotion, "score": confidence, "top_emotions": top_emotions}


