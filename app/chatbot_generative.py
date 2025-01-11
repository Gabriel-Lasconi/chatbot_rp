# chatbot_generative.py

from langchain_ollama import OllamaLLM
from app.emotion_analysis import EmotionDetector
from app.stage_mapping import StageMapper
from app.db import Team, Message

class ChatbotGenerative:
    def __init__(self):
        self.model = OllamaLLM(model="llama3.2")
        self.emotion_detector = EmotionDetector()
        self.stage_mapper = StageMapper()

        self.system_instructions = (
            "You are a helpful assistant analyzing a team's emotional climate and mapping it to Tuckman's stages. "
            "Always begin with a short, friendly greeting, then ask a simple question about the team's current situation or feelings. "
            "Try asking the person about his emotions, how he feels. "
            "Keep your responses concise, ask only brief follow-up questions when you need more information, and avoid lengthy or random questions. "
            "Do not repeat instructions or disclaimers."
            "Focus on emotional cues and team dynamics, and maintain a polite, clear, and context-aware dialogue."
        )

        # ephemeral dictionary to track lines since final stage
        self.lines_since_final_stage = {}

    @property
    def stage_mapper(self):
        return self._stage_mapper

    @stage_mapper.setter
    def stage_mapper(self, value):
        self._stage_mapper = value

    def _load_team_state(self, db, team_name: str):
        team = db.query(Team).filter(Team.name == team_name).first()
        if not team:
            team = Team(name=team_name, current_stage="Uncertain", stage_confidence=0.0)
            db.add(team)
            db.commit()
            db.refresh(team)
        return team

    def _build_prompt(self, conversation_str: str, user_message: str) -> str:
        prompt = (
            f"<<SYS>>\n{self.system_instructions}\n<</SYS>>\n\n"
            f"{conversation_str}\n"
            f"User: {user_message}\n"
            "Assistant:"
        )
        return prompt

    def _generate_response(self, conversation_str: str, user_message: str) -> str:
        prompt = self._build_prompt(conversation_str, user_message)
        response = self.model.invoke(input=prompt)
        return response.strip()

    def process_line(self, db, team_name: str, text: str):
        """
        Insert message, detect top-5 emotions, update distribution, finalize stage if threshold exceeded.
        Return: (bot_response, final_stage, feedback, accum_dist)
        """
        team = self._load_team_state(db, team_name)

        # Insert user message
        user_msg = Message(team_id=team.id, role="User", text=text)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # Detect top-5 emotions
        emotion_results = self.emotion_detector.detect_emotion(text, top_n=5)
        top5_emotions = emotion_results["top_emotions"]

        # Convert them to a distribution
        line_distribution = self._stage_mapper.get_stage_distribution(top5_emotions)

        # Load existing distribution
        accum_dist = team.load_accum_distrib()
        if not accum_dist:
            accum_dist = {stg: 0.0 for stg in self._stage_mapper.stage_emotion_map.keys()}

        # Add the line's distribution, re-normalize
        for stg, val in line_distribution.items():
            accum_dist[stg] += val
        total_sum = sum(accum_dist.values())
        if total_sum > 0.0:
            for stg in accum_dist:
                accum_dist[stg] = accum_dist[stg] / total_sum

        team.num_lines += 1
        team.save_accum_distrib(accum_dist)
        db.commit()

        # ephemeral lines tracking
        if team_name not in self.lines_since_final_stage:
            self.lines_since_final_stage[team_name] = 0
        self.lines_since_final_stage[team_name] += 1

        final_stage = None
        feedback = None

        # If we have >= 3 lines, see if best_sum > 0.5
        if team.num_lines >= 3:
            best_sum = 0.0
            best_stage = None
            for s, v in accum_dist.items():
                if v > best_sum:
                    best_sum = v
                    best_stage = s

            if best_sum > 0.5:
                team.current_stage = best_stage
                db.commit()
                # produce feedback if lines_since_final_stage >= 5
                if self.lines_since_final_stage[team_name] >= 5:
                    final_stage = best_stage
                    feedback = self._stage_mapper.get_feedback_for_stage(best_stage)
                    self.lines_since_final_stage[team_name] = 0

        # Build conversation string for prompt
        messages = db.query(Message).filter(Message.team_id == team.id).order_by(Message.id).all()
        lines_for_prompt = []
        for msg in messages:
            if msg.role.lower() == "assistant":
                lines_for_prompt.append(f"Assistant: {msg.text}")
            else:
                lines_for_prompt.append(f"User: {msg.text}")
        conversation_str = "\n".join(lines_for_prompt)

        # Generate assistant response
        bot_response = self._generate_response(conversation_str, text)

        assistant_msg = Message(
            team_id=team.id,
            role="Assistant",
            text=bot_response,
            detected_emotion="(multiple top-5 used)",
            stage_at_time=final_stage if final_stage else "Uncertain"
        )
        db.add(assistant_msg)
        db.commit()

        return bot_response, final_stage, feedback, accum_dist

    def analyze_conversation_db(self, db, team_name: str, lines: list):
        """
        Pass multiple lines. We return final_stage, feedback, and final accum_dist.
        """
        final_stage = None
        feedback = None
        accum_dist = {}

        for line in lines:
            bot_msg, concluded_stage, concluded_feedback, accum_dist = self.process_line(db, team_name, line)
            if concluded_stage:
                final_stage = concluded_stage
                feedback = concluded_feedback
                break

        return final_stage, feedback, accum_dist

    def reset_team(self, db, team_name: str):
        team = db.query(Team).filter(Team.name == team_name).first()
        if team:
            team.current_stage = "Uncertain"
            team.stage_confidence = 0.0
            # reset distribution
            dist_reset = {stg: 0.0 for stg in self._stage_mapper.stage_emotion_map.keys()}
            team.save_accum_distrib(dist_reset)
            team.num_lines = 0
            db.query(Message).filter(Message.team_id == team.id).delete()
            db.commit()

        if team_name in self.lines_since_final_stage:
            del self.lines_since_final_stage[team_name]
