from langchain_ollama import OllamaLLM
from app.emotion_analysis import EmotionDetector
from app.stage_mapping import StageMapper
from app.db import Team, Message

class ChatbotGenerative:
    def __init__(self):
        """
        Initializes the chatbot using the Ollama LLaMA model.
        """
        self.model = OllamaLLM(model="llama3.2")
        self.emotion_detector = EmotionDetector()
        self.stage_mapper = StageMapper()

        self.system_instructions = (
            "You are a helpful assistant analyzing a team's emotional climate and mapping it to Tuckman's stages. "
            "Always begin with a short, friendly greeting, then ask a simple question about the team's current situation or feelings."
            "Try asking the person about his emotions, how he feels. "
            "Keep your responses concise, ask only brief follow-up questions when you need more information, and avoid lengthy or random questions. "
            "Do not repeat instructions or disclaimers. If you have enough context to identify a stage, provide short, stage-specific feedback; "
            "otherwise, gather more relevant details with minimal elaboration. "
            "Focus on emotional cues and team dynamics, and maintain a polite, clear, and context-aware dialogue."
        )

        # Dictionary to track how many new lines have arrived
        # since the last final stage was found, for each team_name.
        # This is ephemeral: if the server restarts, these counters reset.
        self.lines_since_final_stage = {}  # e.g. { team_name: int }

    def _load_team_state(self, db, team_name: str):
        """
        Retrieve or create a Team record by name. Returns the Team ORM object.
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
        Main approach:
          1. Insert user message into DB.
          2. Detect top-5 emotions -> get normalized distribution for this line.
          3. Accumulate distribution in DB's accum_distribution, also normalized.
          4. If we have >= 3 total lines for this team, see if any stage > 0.7. If so, store that stage.
          5. But do not produce final stage feedback if we haven't had at least 3 new lines since last finalization.
          6. Generate an assistant response, store it, and possibly produce feedback.
        """
        team = self._load_team_state(db, team_name)

        # Insert the user message into DB
        user_msg = Message(team_id=team.id, role="User", text=text)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # Detect top-5 emotions
        emotion_results = self.emotion_detector.detect_emotion(text, top_n=5)
        top5_emotions = emotion_results["top_emotions"]
        print("Top-5 Emotions:", top5_emotions)

        # Convert them to a distribution
        line_distribution = self.stage_mapper.get_stage_distribution(top5_emotions)
        print("Line Distribution:", line_distribution)

        # Load the existing distribution from the DB
        accum_dist = team.load_accum_distrib()
        if not accum_dist:
            accum_dist = {stg: 0.0 for stg in self.stage_mapper.stage_emotion_map.keys()}

        # Add the line's distribution, then re-normalize
        for stg, val in line_distribution.items():
            accum_dist[stg] += val
        total_sum = sum(accum_dist.values())
        if total_sum > 0:
            for stg in accum_dist:
                accum_dist[stg] = accum_dist[stg] / total_sum

        # Save the updated distribution + increment lines
        team.num_lines += 1
        team.save_accum_distrib(accum_dist)
        db.commit()

        # lines_since_final_stage ephemeral logic
        # If we have no entry yet, initialize to 0
        if team_name not in self.lines_since_final_stage:
            self.lines_since_final_stage[team_name] = 0

        self.lines_since_final_stage[team_name] += 1

        # Decide if we can finalize a stage or not
        final_stage = None
        stage_feedback = None

        # Only if we have >= 3 total lines in DB, let's see if any stage is > 0.5
        if team.num_lines >= 3:
            best_stage, best_sum = None, 0.0
            for stg, val in accum_dist.items():
                if val > best_sum:
                    best_sum = val
                    best_stage = stg

            print("Best stage sum:", best_sum, "Stage:", best_stage)

            if best_sum > 0.5:
                # Store that stage in DB
                team.current_stage = best_stage
                db.commit()
                # Only produce feedback if we have at least 5 new lines
                # since last final stage conclusion
                if self.lines_since_final_stage[team_name] >= 5:
                    final_stage = best_stage
                    stage_feedback = self.stage_mapper.get_feedback_for_stage(best_stage)
                    # reset ephemeral lines_since_final_stage
                    self.lines_since_final_stage[team_name] = 0

        # Build conversation string from all messages
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

        return bot_response, final_stage, stage_feedback


    def analyze_conversation_db(self, db, team_name: str, lines: list):
        """
        Multi-line approach: pass a list of user lines in bulk.
        We'll feed them one by one to process_line with the new distribution logic.
        If we finalize stage early, we stop. If not, we get no final stage after all lines.
        """
        final_stage = None
        feedback = None

        for line in lines:
            bot_msg, concluded_stage, concluded_feedback = self.process_line(db, team_name, line)
            if concluded_stage:
                final_stage = concluded_stage
                feedback = concluded_feedback
                # we break once a stage is concluded
                break
        return final_stage, feedback

    def reset_team(self, db, team_name: str):
        """
        Clears distribution logic plus DB messages. Also resets ephemeral line counters.
        """
        team = db.query(Team).filter(Team.name == team_name).first()
        if team:
            team.current_stage = "Uncertain"
            team.stage_confidence = 0.0
            db.query(Message).filter(Message.team_id == team.id).delete()
            # also reset distribution
            dist_reset = {stg: 0.0 for stg in self.stage_mapper.stage_emotion_map.keys()}
            team.save_accum_distrib(dist_reset)
            team.num_lines = 0
            db.commit()

        # reset ephemeral lines_since_final_stage
        if team_name in self.lines_since_final_stage:
            del self.lines_since_final_stage[team_name]
