# stage_mapping.py

from langchain_ollama import OllamaLLM
from sqlalchemy.orm import Session

from app.db import Message, Team, Member


class StageMapper:
    def __init__(self):
        """
        Initializes the StageMapper with mappings from emotions to Tuckman's stages
        and sets up the LLaMA language model for generating feedback.
        """
        self.stage_emotion_map = {
            "Forming": [
                "excitement", "anticipation", "curiosity", "interest", "hope",
                "mild anxiety", "nervousness", "cautious optimism", "insecurity"
            ],
            "Storming": [
                "anger", "frustration", "tension", "resentment", "hostility",
                "disappointment", "fear of conflict", "defensiveness",
                "uncertainty about direction", "discouragement", "rivalry",
                "unfairness", "conflict"
            ],
            "Norming": [
                "acceptance of roles", "feel of cohesion", "trust", "renewed hope",
                "commitment", "calm", "serenity", "empathy", "camaraderie",
                "relief from resolved conflict", "unity"
            ],
            "Performing": [
                "confidence in team", "mutual respect", "enthusiasm about goals",
                "flow", "synergy", "empowerment", "self-confidence", "pride in work",
                "accomplishment", "joy in collaboration", "satisfaction with outcomes"
            ],
            "Adjourning": [
                "sense of loss", "nostalgia for the group", "sadness about closure",
                "relief from completion", "thankfulness for the experience",
                "disorientation from change", "reflection on achievements",
                "uncertainty about next steps", "enthusiasm for the future", "closure"
            ]
        }

        self.llama_model = OllamaLLM(model="llama3.2")

    # ========================================================
    #   STAGE DISTRIBUTION FUNCTIONS
    # ========================================================

    def get_stage_distribution(self, top5_emotions):
        """
        Calculates the distribution of Tuckman stages based on top-5 emotions from a single message.

        Args:
            top5_emotions (list): A list of dictionaries containing emotion labels and their confidence scores.

        Returns:
            dict: A normalized distribution of stages with their corresponding activation values.
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
        Calculates the distribution of Tuckman stages based on accumulated emotions from all messages.

        Args:
            accum_emotions (dict): A dictionary of all emotions with their accumulated confidence scores.

        Returns:
            dict: A normalized distribution of stages with their corresponding activation values.
        """
        distribution = {stage: 0.0 for stage in self.stage_emotion_map}

        for emotion_label, value in accum_emotions.items():
            stage_for_emo = self._which_stage(emotion_label)
            if stage_for_emo:
                distribution[stage_for_emo] += value

        total_sum = sum(distribution.values())
        if total_sum > 0:
            for stg in distribution:
                distribution[stg] /= total_sum

        return distribution

    #========================================================
    #   HELPERS
    # ========================================================

    def _which_stage(self, emotion_label):
        """
        Determines which Tuckman stage an emotion belongs to.

        Args:
            emotion_label (str): The emotion label to classify.

        Returns:
            str or None: The stage name if found, else None.
        """
        for stage, emos in self.stage_emotion_map.items():
            if emotion_label in emos:
                return stage
        return None

    # ========================================================
    #   FEEDBACK GENERATION FUNCTIONS
    # ========================================================

    def get_team_feedback(self, db: Session, team_id: int, stage: str) -> str:
        """
        Generates team-level feedback by analyzing messages from all team members.

        Args:
            db (Session): The database session.
            team_id (int): The ID of the team.
            stage (str): The current stage of the team.

        Returns:
            str: The generated feedback.
        """
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return "Team not found."

        messages = (
            db.query(Message)
            .join(Member)
            .filter(Member.team_id == team_id)
            .order_by(Message.id)
            .all()
        )

        conversation_str = ""
        for msg in messages:
            role = msg.role.capitalize()
            conversation_str += f"{role}: {msg.text}\n"

        prompt = f"""<<SYS>>
        You are an assistant that analyzes team-wide conversations and provides structured feedback.
        Based on the full team conversation below, provide the following:
        
        FEEDBACK:
        1. A SUMMARY OF THE TEAM'S PROBLEMS
        2. A SHORT EXPLANATION WHY THIS DIAGNOSTIC (Tuckman stage: {stage}) FITS BEST
        3. POSITIVE AND CONSTRUCTIVE FEEDBACK FOR THE TEAM
        
        <</SYS>>
        
        Team conversation:
        {conversation_str}
        
        Based on this, the team's current stage is: {stage}.
        Provide feedback in the requested format. Avoid text in bold, bullet points or writing the feedback in an ordered list. Write it in paragraphs.
        """

        try:
            response = self.llama_model.invoke(input=prompt).strip()
            return response
        except Exception as e:
            print(f"[ERROR in get_team_feedback] {e}")
            return "An error occurred while generating team feedback."

    def get_personal_feedback(self, db: Session, member_id: int, stage: str) -> str:
        """
        Generates personal feedback for a specific team member by analyzing their messages.

        Args:
            db (Session): The database session.
            member_id (int): The ID of the member.
            stage (str): The current stage of the member.

        Returns:
            str: The generated personal feedback.
        """
        messages = (
            db.query(Message)
            .filter(Message.member_id == member_id)
            .order_by(Message.id)
            .all()
        )

        conversation_str = ""
        for msg in messages:
            role = msg.role.capitalize()
            conversation_str += f"{role}: {msg.text}\n"

        prompt = f"""<<SYS>>
        You are an assistant that analyzes a user's personal conversation and provides structured feedback.
        Based on the full personal conversation below, provide the following:
        
        FEEDBACK:
        1. A SUMMARY OF THE USER'S PROBLEMS
        2. A SHORT EXPLANATION WHY THIS DIAGNOSTIC (Tuckman stage: {stage}) FITS BEST
        3. POSITIVE AND CONSTRUCTIVE FEEDBACK FOR THE USER
        
        <</SYS>>
        
        User conversation:
        {conversation_str}
        
        Based on this, the user's current stage is: {stage}.
        Provide feedback in the requested format. Avoid text in bold, bullet points or writing the feedback in an ordered list. Write it in paragraphs.
        """

        try:
            response = self.llama_model.invoke(input=prompt).strip()
            return response
        except Exception as e:
            print(f"[ERROR in get_personal_feedback] {e}")
            return "An error occurred while generating personal feedback."
