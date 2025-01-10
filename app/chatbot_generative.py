from langchain_ollama import OllamaLLM
from app.emotion_analysis import EmotionDetector
from app.stage_mapping import StageMapper
from app.db import SessionLocal, Team, Message

class ChatbotGenerative:
    def __init__(self):
        """
        Initializes the chatbot using the Ollama LLaMA model.
        """
        self.model = OllamaLLM(model="llama3.2")
        self.emotion_detector = EmotionDetector()
        self.stage_mapper = StageMapper()

        # System instructions remain the same
        self.system_instructions = (
            "You are a concise assistant analyzing a team's emotional climate "
            "and mapping it to Tuckman's stages. Only ask short follow-up questions "
            "Avoid lengthy elaborations or repeating instructions."
        )

        # We'll store partial distributions for multiple messages in memory.
        # Once we have at least 3 messages, we see if any stage's sum > 0.7
        # We'll also keep track in the DB the team's current stage, but it
        # won't finalize until the distribution surpasses 70%.
        # This approach ensures multi-message accumulation.
        #
        # For demonstration, we accumulate ephemeral data here. In a real system,
        # you might store partial distributions in the DB too.

    def _load_team_state(self, db, team_name: str):
        """
        Retrieve or create a Team record by name. Returns the Team ORM object.
        If you want to track partial distributions in DB, you'd adapt this approach.
        """
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
        1. Insert user message -> DB
        2. Use top-5 emotions -> compute stage distribution from that line
        3. Accumulate distribution in the team's DB columns accum_distribution + num_lines
        4. If we have >= 3 lines and a stage sum > 0.7, finalize that stage
        5. Generate an assistant response
        6. If we finalize stage, store it in DB
        """
        # 1. Load or create team
        team = self._load_team_state(db, team_name)

        # Insert the user message
        user_msg = Message(team_id=team.id, role="User", text=text)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # 2. Detect top-5 emotions
        emotion_results = self.emotion_detector.detect_emotion(text, top_n=5)
        top5_emotions = emotion_results["top_emotions"]  # e.g. [{"label": "...", "score":0.3}, ...]
        print("Top-5 Emotions:", top5_emotions)

        # Convert them to a stage distribution for this single line
        line_distribution = self.stage_mapper.get_stage_distribution(top5_emotions)
        print("Line Distribution:", line_distribution)

        # 3. Load the existing distribution from the DB, update it, then save
        accum_dist = team.load_accum_distrib()  # returns a dict of stage->float
        if not accum_dist:  # If empty, init with 0.0 for each stage
            accum_dist = {stg: 0.0 for stg in self.stage_mapper.stage_emotion_map.keys()}

        for stg, val in line_distribution.items():
            accum_dist[stg] = accum_dist.get(stg, 0.0) + val

        team.num_lines += 1
        team.save_accum_distrib(accum_dist)
        db.commit()

        final_stage = None
        stage_feedback = None

        # 4. If we have >= 3 lines, check if any stage sum > 0.7
        print(team.num_lines)
        if team.num_lines >= 3:
            # Find the stage with the highest sum
            best_stage = None
            best_sum = 0.0
            for stg, total_val in accum_dist.items():
                if total_val > best_sum:
                    best_sum = total_val
                    best_stage = stg

            print("Best stage sum:", best_sum, "Stage:", best_stage)
            if best_sum > 0.7:
                final_stage = best_stage
                stage_feedback = self.stage_mapper.get_feedback_for_stage(best_stage)
                team.current_stage = best_stage
                db.commit()

        # Build conversation string from existing messages
        messages = db.query(Message).filter(Message.team_id == team.id).order_by(Message.id).all()
        lines_for_prompt = []
        for msg in messages:
            if msg.role.lower() == "assistant":
                lines_for_prompt.append(f"Assistant: {msg.text}")
            else:
                lines_for_prompt.append(f"User: {msg.text}")
        conversation_str = "\n".join(lines_for_prompt)

        # 5. Generate assistant response
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

        return bot_response, final_stage, stage_feedback

    def analyze_conversation_db(self, db, team_name: str, lines: list):
        """
        Multi-line approach: pass a list of user lines in bulk.
        We'll feed them one by one to process_line with the new accumulation logic.
        If we finalize stage early, we stop. If not, we get no final stage after all lines.
        """
        final_stage = None
        feedback = None

        for line in lines:
            bot_msg, concluded_stage, concluded_feedback = self.process_line(db, team_name, line)
            if concluded_stage:
                final_stage = concluded_stage
                feedback = concluded_feedback
                break
        return final_stage, feedback

    def reset_team(self, db, team_name: str):
        """
        Clear the ephemeral distribution logic plus DB messages.
        """
        team = db.query(Team).filter(Team.name == team_name).first()
        if team:
            team.current_stage = "Uncertain"
            team.stage_confidence = 0.0
            # Remove ephemeral accum_distrib
            if hasattr(team, "accum_distrib"):
                delattr(team, "accum_distrib")
            if hasattr(team, "num_lines"):
                delattr(team, "num_lines")

            # Clear messages
            db.query(Message).filter(Message.team_id == team.id).delete()
            db.commit()
