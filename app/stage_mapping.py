# stage_mapping.py

from langchain_ollama import OllamaLLM
from sqlalchemy.orm import Session

from app.db import Message, Team, Member


class StageMapper:
    def __init__(self):
        """
        Maps emotions to Tuckman stages. Also provides short feedback for any stage.
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

    def get_team_feedback(self, db: Session, team_id: int, stage: str) -> str:
        """
        Generate team-level feedback by analyzing messages from all members of a team.
        """
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return "Team not found."

        # Fetch messages for all members
        messages = (
            db.query(Message)
            .join(Member)
            .filter(Member.team_id == team_id)
            .order_by(Message.id)
            .all()
        )

        # Build conversation string
        conversation_str = ""
        for msg in messages:
            role = msg.role.capitalize()
            conversation_str += f"{role}: {msg.text}\n"

        # Construct prompt
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

        # Invoke LLaMA
        try:
            response = self.llama_model.invoke(input=prompt).strip()
            return response
        except Exception as e:
            print(f"[ERROR in get_team_feedback] {e}")
            return "An error occurred while generating team feedback."

    def get_personal_feedback(self, db: Session, member_id: int, stage: str) -> str:
        """
        Generate personal feedback for a specific team member by analyzing their messages.
        """
        # Retrieve messages for this member
        messages = (
            db.query(Message)
            .filter(Message.member_id == member_id)
            .order_by(Message.id)
            .all()
        )

        # Build conversation string
        conversation_str = ""
        for msg in messages:
            role = msg.role.capitalize()
            conversation_str += f"{role}: {msg.text}\n"

        # Construct prompt
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

        # Invoke LLaMA
        try:
            response = self.llama_model.invoke(input=prompt).strip()
            return response
        except Exception as e:
            print(f"[ERROR in get_personal_feedback] {e}")
            return "An error occurred while generating personal feedback."

