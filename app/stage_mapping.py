#app/stage_mapping.py - class for stage-emotion mappings and feedback.


class StageMapper:
    def __init__(self):
        # emotions corresponding to each stage taken from table in literature review
        self.stage_emotion_map = {
            "Forming": ["excitement", "anticipation", "anxiety", "curiosity", "eagerness"],
            "Storming": ["frustration", "tension", "defensiveness", "conflict", "uncertainty"],
            "Norming": ["relief", "trust", "acceptance", "cohesion", "camaraderie", "optimism"],
            "Performing": ["confidence", "enthusiasm", "pride", "accomplishment", "satisfaction", "cohesion"],
            "Adjourning": ["nostalgia", "closure", "sadness", "reflection"]
        }
        # generic feedback given for each stage (just a base to start from)
        self.stage_feedback = {
            "Forming": "It appears your team is in the Forming stage. This is a time for building trust and getting acquainted. Encourage open communication and help team members understand their roles.",
            "Storming": "Your team seems to be in the Storming stage. Tensions and conflicts may arise. Consider addressing issues openly, clarifying goals, and building mutual respect.",
            "Norming": "Your team is in the Norming stage. Members are learning to collaborate effectively. Reinforce positive behavior, celebrate small wins, and encourage further cohesion.",
            "Performing": "Your team is Performing well. They are likely functioning at a high level. Maintain the momentum, reward achievements, and consider new challenges to keep motivation high.",
            "Adjourning": "Your team appears to be in the Adjourning stage. It’s time to reflect on the journey, acknowledge accomplishments, and ensure a supportive closure. Discuss lessons learned and future opportunities."
        }

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
        Get feedback for a specific team stage.

        Args:
            stage (str): Team stage.

        Returns:
            str: Feedback for the stage.
        """
        return self.stage_feedback.get(stage, "No feedback available for this stage.")
