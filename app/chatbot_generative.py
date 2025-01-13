from langchain_ollama import OllamaLLM
from app.emotion_analysis import EmotionDetector
from app.stage_mapping import StageMapper
from app.db import Team, Member, Message

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
            "Do not repeat instructions or disclaimers. "
            "Focus on emotional cues and team dynamics, and maintain a polite, clear, and context-aware dialogue."
        )

        self.lines_since_final_stage = {}

    @property
    def stage_mapper(self):
        return self._stage_mapper

    @stage_mapper.setter
    def stage_mapper(self, value):
        self._stage_mapper = value

    def _load_team(self, db, team_name: str):
        team = db.query(Team).filter(Team.name == team_name).first()
        if not team:
            team = Team(name=team_name, current_stage="Uncertain", stage_confidence=0.0)
            db.add(team)
            db.commit()
            db.refresh(team)
        return team

    def _load_member(self, db, team, member_name: str):
        member = db.query(Member).filter(
            Member.name == member_name,
            Member.team_id == team.id
        ).first()
        if not member:
            member = Member(name=member_name, team_id=team.id, current_stage="Uncertain", stage_confidence=0.0)
            db.add(member)
            db.commit()
            db.refresh(member)
        return member

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

    def _classify_message_relevance(self, text: str) -> bool:
        classification_prompt = (
            "Classify the following user message as either 'Valuable' or 'Skip'. "
            "The output should be one word, either 'Valuable' or 'Skip'!:\n\n"
            f"User message: \"{text}\"\n\n"
            "Rules:\n"
            "1. If it references feelings, emotions, or team dynamics (e.g., conflicts, roles, tasks, trust, frustration, etc.), output 'Valuable'.\n"
            "2. If it is only a greeting, small talk, or not about the team's emotional state, output 'Skip'.\n"
            "3. Output exactly one word: 'Valuable' or 'Skip'."
        )
        response = self.model.invoke(input=classification_prompt).strip()
        print("[DEBUG classify_message_relevance] =>", response)
        return response.lower().startswith("valuable")

    def _compute_team_stage(self, db, team):
        """
        After we update a member's stage, we compute the entire team's
        numeric average stage (if possible) and store the combined distribution
        from all members in team.stage_distribution.
        """
        numeric_map = {
            "Forming": 0,
            "Storming": 1,
            "Norming": 2,
            "Performing": 3,
            "Adjourning": 4,
            "Uncertain": None
        }

        stage_names = ["Forming", "Storming", "Norming", "Performing", "Adjourning"]

        # 1) Compute numeric stage average
        valid_stage_values = []
        for m in team.members:
            if m.current_stage in numeric_map and numeric_map[m.current_stage] is not None:
                valid_stage_values.append(numeric_map[m.current_stage])

        if not valid_stage_values:
            # If no numeric stages are known, we'll keep the team at "Uncertain"
            team.current_stage = "Uncertain"
        else:
            # Average them
            avg_val = sum(valid_stage_values) / len(valid_stage_values)
            nearest_stage_idx = int(round(avg_val))
            if nearest_stage_idx < 0:
                nearest_stage_idx = 0
            if nearest_stage_idx > 4:
                nearest_stage_idx = 4
            team.current_stage = stage_names[nearest_stage_idx]

        # 2) Combine distribution from all members
        combined = {st: 0.0 for st in stage_names}
        num_members_with_dist = 0
        for mem in team.members:
            dist = mem.load_accum_distrib()
            if dist:
                num_members_with_dist += 1
                for st in stage_names:
                    combined[st] += dist.get(st, 0.0)
        if num_members_with_dist > 0:
            for st in combined:
                combined[st] /= num_members_with_dist
        else:
            combined = {}

        # 3) Save to DB
        team.save_team_distribution(combined)
        db.commit()

    def process_line(self, db, team_name: str, member_name: str, text: str):
        """
        Insert message from user, detect if valuable, do emotion analysis if so,
        update that member's distribution, finalize their stage if confident,
        then ALWAYS recompute the team stage. Finally, build conversation and respond.
        Returns: (bot_response, final_stage, feedback, member_dist, last_emotion_dist)
        """
        # 1) Load or create the team & member
        team = self._load_team(db, team_name)
        member = self._load_member(db, team, member_name)

        # 2) Insert the user message in DB
        user_msg = Message(member_id=member.id, role="User", text=text)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # Prepare
        accum_dist = member.load_accum_distrib()
        if not accum_dist:
            accum_dist = {stg: 0.0 for stg in self._stage_mapper.stage_emotion_map.keys()}

        final_stage = None
        feedback = None
        last_emotion_dist = {}  # for the last message's top-5 emotions

        is_valuable = self._classify_message_relevance(text)
        if is_valuable:
            # 1) detect top-5 emotions
            emotion_results = self.emotion_detector.detect_emotion(text, top_n=5)
            top5_emotions = emotion_results["top_emotions"]

            # store them in the message
            dist_for_message = {emo["label"]: emo["score"] for emo in top5_emotions}
            user_msg.save_top_emotion_distribution(dist_for_message)
            db.commit()

            # also return them so the front-end can show them
            last_emotion_dist = dist_for_message

            # 2) map to Tuckman distribution
            line_distribution = self._stage_mapper.get_stage_distribution(top5_emotions)
            for stg, val in line_distribution.items():
                accum_dist[stg] += val

            # re-normalize
            total_sum = sum(accum_dist.values())
            if total_sum > 0.0:
                for stg in accum_dist:
                    accum_dist[stg] /= total_sum

            # store back
            member.num_lines += 1
            member.save_accum_distrib(accum_dist)
            db.commit()

            # ephemeral lines
            key_for_ephemeral = (team_name, member_name)
            if key_for_ephemeral not in self.lines_since_final_stage:
                self.lines_since_final_stage[key_for_ephemeral] = 0
            self.lines_since_final_stage[key_for_ephemeral] += 1

            # finalize stage for member if distribution is big enough
            if member.num_lines >= 3:
                best_sum = 0.0
                best_stage = None
                for s, v in accum_dist.items():
                    if v > best_sum:
                        best_sum = v
                        best_stage = s
                if best_sum > 0.5:
                    member.current_stage = best_stage
                    db.commit()
                    if self.lines_since_final_stage[key_for_ephemeral] >= 3:
                        final_stage = best_stage
                        feedback = self._stage_mapper.get_feedback_for_stage(best_stage)
                        self.lines_since_final_stage[key_for_ephemeral] = 0

        # Recompute the entire team's stage
        self._compute_team_stage(db, team)

        # Build conversation
        all_msgs = []
        for mem in team.members:
            for m in mem.messages:
                all_msgs.append(m)
        all_msgs.sort(key=lambda x: x.id)

        lines_for_prompt = []
        for msg in all_msgs:
            if msg.role.lower() == "assistant":
                lines_for_prompt.append(f"Assistant: {msg.text}")
            else:
                # optionally show "User (mem.name)"
                lines_for_prompt.append(
                    f"User ({mem.name}): {msg.text}" if msg.member_id == mem.id else f"User: {msg.text}"
                )
        conversation_str = "\n".join(lines_for_prompt)

        # get final bot answer
        bot_response = self._generate_response(conversation_str, text)

        # insert assistant's response
        assistant_msg = Message(
            member_id=member.id,
            role="Assistant",
            text=bot_response,
            detected_emotion="(Top-5 used)" if is_valuable else "(Skipped)",
            stage_at_time=final_stage if final_stage else "Uncertain"
        )
        db.add(assistant_msg)
        db.commit()

        return bot_response, final_stage, feedback, accum_dist, last_emotion_dist

    def analyze_conversation_db(self, db, team_name: str, member_name: str, lines: list):
        final_stage = None
        feedback = None
        accum_dist = {}

        for line in lines:
            bot_msg, concluded_stage, concluded_feedback, accum_dist, _ = self.process_line(
                db, team_name, member_name, line
            )
            if concluded_stage:
                final_stage = concluded_stage
                feedback = concluded_feedback
        return final_stage, feedback, accum_dist

    def reset_team(self, db, team_name: str):
        team = db.query(Team).filter(Team.name == team_name).first()
        if team:
            team.current_stage = "Uncertain"
            team.stage_confidence = 0.0
            # reset all members
            for member in team.members:
                member.current_stage = "Uncertain"
                member.stage_confidence = 0.0
                dist_reset = {stg: 0.0 for stg in self._stage_mapper.stage_emotion_map.keys()}
                member.save_accum_distrib(dist_reset)
                member.num_lines = 0
                db.query(Message).filter(Message.member_id == member.id).delete()
                db.commit()
            db.commit()

        # ephemeral counters
        keys_to_delete = []
        for (t_name, m_name) in self.lines_since_final_stage:
            if t_name == team_name:
                keys_to_delete.append((t_name, m_name))
        for k in keys_to_delete:
            del self.lines_since_final_stage[k]
