# emotion_analysis.py

from transformers import pipeline

class EmotionDetector:
    def __init__(self):
        """
        Initializes the EmotionDetector with a zero-shot classification pipeline
        and defines a list of candidate emotions mapped to Tuckman's stages.
        """
        self.zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

        # Candidate emotions categorized by Tuckman's stages
        self.candidate_emotions = [
            # Forming
            "excitement", "anticipation", "curiosity", "interest", "hope",
            "mild anxiety", "nervousness", "cautious optimism", "insecurity",

            # Storming
            "anger", "frustration", "tension", "resentment", "hostility",
            "disappointment", "fear of conflict", "defensiveness", "uncertainty about direction",
            "discouragement", "rivalry", "unfairness", "conflict",

            # Norming
            "acceptance of roles", "feel of cohesion", "trust", "renewed hope",
            "commitment", "calm", "serenity", "empathy", "camaraderie",
            "relief from resolved conflict", "unity",

            # Performing
            "confidence in team", "mutual respect", "enthusiasm about goals",
            "flow", "synergy", "empowerment", "self-confidence", "pride in work",
            "accomplishment", "joy in collaboration", "satisfaction with outcomes",

            # Adjourning
            "sense of loss", "nostalgia for the group", "sadness about closure",
            "relief from completion", "thankfulness for the experience",
            "disorientation from change", "reflection on achievements", "uncertainty about next steps",
            "enthusiasm for the future", "closure"
        ]

    # ========================================================
    #   EMOTION DETECTION FUNCTIONS
    # ========================================================

    def detect_emotion(self, text: str, top_n: int = 5):
        """
        Detects the top emotions in the given text using zero-shot classification.

        Args:
            text (str): The text to analyze.
            top_n (int): The number of top emotions to return.

        Returns:
            dict: Contains the dominant emotion, its confidence score, and a list of top emotions with scores.
        """
        if not text.strip():
            return {
                "label": "uncertainty",
                "score": 1.0,
                "top_emotions": [{"label": "uncertainty", "score": 1.0}]
            }

        result = self.zero_shot_classifier(text, self.candidate_emotions)

        top_emotions = [
            {"label": label, "score": score}
            for label, score in zip(result["labels"], result["scores"])
        ]
        top_emotions = top_emotions[:top_n]

        dominant_emotion = top_emotions[0]["label"]
        confidence = top_emotions[0]["score"]

        return {
            "label": dominant_emotion,
            "score": confidence,
            "top_emotions": top_emotions
        }
