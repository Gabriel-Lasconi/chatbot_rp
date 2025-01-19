import re

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
            team = Team(name=team_name, current_stage="Uncertain")
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
            member = Member(name=member_name, team_id=team.id, current_stage="Uncertain")
            db.add(member)
            db.commit()
            db.refresh(member)
        return member

    def _extract_unique_members_via_llama(self, chat_log: str):
        """
        Uses the LLama model to extract a list of unique team member names from the chat log.
        Ensures that only active participants (who have sent messages) are included.
        """
        prompt = (
            "Extract a list of unique team member names who have sent messages in the following chat log. "
            "Only include the names of people who have actively participated in the conversation, not names mentioned in the messages.\n\n"
            f"Chat Log:\n{chat_log}\n\n"
            "List of team members:"
        )

        response = self.model.invoke(input=prompt).strip()

        # Assume the response is a comma-separated list of names
        # e.g., "Sarp Onkahraman, Archie Ιμαμίδης, Max 🔨"
        members = [name.strip() for name in response.split(",") if name.strip()]

        # Normalize member names to prevent duplicates
        normalized_members = self._normalize_member_names(members)

        return normalized_members

    def _normalize_member_names(self, members):
        """
        Normalizes member names by removing emojis and trimming whitespace.
        This helps in preventing duplicates caused by formatting differences.
        """
        normalized = []
        for name in members:
            # Remove emojis and non-alphanumeric characters
            name_clean = re.sub(r'[^\w\s]', '', name)
            name_clean = name_clean.strip()
            if name_clean and name_clean not in normalized:
                normalized.append(name_clean)
        return normalized

    def _extract_members_and_messages(self, chat_log: str):
        """
        Extracts members and messages from the provided chat log.
        Handles both formats:
        1. [timestamp] Name: message
        2. Name: message
        """
        member_message_map = {}

        # Clean the chat log to remove problematic characters
        cleaned_chat_log = re.sub(r"[\u200e]", "", chat_log)

        # Regular expression to match both formats
        pattern = re.compile(r"(?:\[(.*?)\] )?(.*?): (.*)")

        for line in cleaned_chat_log.splitlines():
            match = pattern.match(line)
            if match:
                _, name, message = match.groups()
                if name:  # Ensure we have a valid name
                    if name not in member_message_map:
                        member_message_map[name] = []
                    member_message_map[name].append(message)

        return member_message_map

    def _process_chat_log(self, db, team_name: str, chat_log):
        """
        Processes the entire chat log:
        - Ensures the team exists (creates one if necessary).
        - Extracts members and messages from the chat log.
        - Adds them to the database.
        """
        team = self._load_team(db, team_name)

        # Ensure chat_log is a string
        if isinstance(chat_log, list):
            chat_log = "\n".join(chat_log)

        # Parse the chat log to extract members and their messages
        member_message_map = self._extract_members_and_messages(chat_log)

        # Add members and messages to the database
        for member_name, messages in member_message_map.items():
            member = self._load_member(db, team, member_name)

            for message in messages:
                user_msg = Message(member_id=member.id, role="User", text=message)
                db.add(user_msg)
            db.commit()

        return member_message_map.keys()

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
        After updating each member's accum_distrib,
        compute the 'combined' distribution for the entire team,
        then pick whichever stage has the highest value in that distribution
        as the final team stage.
        """
        stage_names = ["Forming", "Storming", "Norming", "Performing", "Adjourning"]
        combined = {s: 0.0 for s in stage_names}
        num_members = 0

        # Sum up each member's accum_distrib
        for mem in team.members:
            dist = mem.load_accum_distrib()
            if dist:
                num_members += 1
                for stg, val in dist.items():
                    if stg in combined:
                        combined[stg] += val

        # If no members have a distribution, set combined to empty
        if num_members > 0:
            for stg in combined:
                combined[stg] /= num_members
        else:
            combined = {}

        # Save the combined distribution
        team.save_team_distribution(combined)
        db.commit()

        # If combined is empty, set team.current_stage to "Uncertain"
        if not combined or all(v == 0.0 for v in combined.values()):
            team.current_stage = "Uncertain"
            db.commit()
            return

        # Otherwise, find the stage with the maximum value
        best_stage = None
        best_val = -1.0
        for stg, val in combined.items():
            if val > best_val:
                best_val = val
                best_stage = stg

        team.current_stage = best_stage
        db.commit()

    def process_line(self, db, team_name: str, member_name: str, text: str, mode: str = "conversation"):
        """
        Processes a single line of conversation, either in conversation or analysis mode.

        Parameters:
        - db: Database session.
        - team_name: Name of the team.
        - member_name: Name of the member.
        - text: The message text.
        - mode: 'conversation' or 'analysis'. Determines whether to generate assistant responses.

        Returns:
        - If mode is 'conversation':
            (bot_response, final_stage, team_feedback, accum_dist, last_emotion_dist, accum_emotions, personal_feedback)
        - If mode is 'analysis':
            (None, final_stage, team_feedback, accum_dist, last_emotion_dist, accum_emotions, personal_feedback)
        """
        team = self._load_team(db, team_name)
        member = self._load_member(db, team, member_name)

        # Create the new user message
        user_msg = Message(member_id=member.id, role="User", text=text)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # Load existing data
        accum_dist = member.load_accum_distrib()       # Tuckman distribution
        accum_emotions = member.load_accum_emotions()  # overall emotion distribution
        # Load current data from the database
        final_stage = team.load_current_stage()
        team_feedback = team.load_feedback()
        personal_feedback = member.load_personal_feedback()
        if not accum_dist:
            accum_dist = {stg: 0.0 for stg in self._stage_mapper.stage_emotion_map.keys()}
        if not accum_emotions:
            accum_emotions = {}

        last_emotion_dist = {}

        # Check message relevance
        is_valuable = self._classify_message_relevance(text)
        if is_valuable:
            # Detect top-5 emotions for this message
            emotion_results = self.emotion_detector.detect_emotion(text, top_n=5)
            top5_emotions = emotion_results["top_emotions"]

            # Store top-5 in the message row
            dist_for_message = {emo["label"]: emo["score"] for emo in top5_emotions}
            user_msg.save_top_emotion_distribution(dist_for_message)
            db.commit()

            last_emotion_dist = dist_for_message

            # Update accum_emotions (the entire user's total emotional distribution)
            for e_dict in top5_emotions:
                lbl = e_dict["label"]
                conf = e_dict["score"]
                accum_emotions[lbl] = accum_emotions.get(lbl, 0.0) + conf

            # Re-normalize accum_emotions
            sum_emotions = sum(accum_emotions.values())
            if sum_emotions > 0.0:
                for e_lbl in accum_emotions:
                    accum_emotions[e_lbl] = accum_emotions[e_lbl] / sum_emotions

            member.save_accum_emotions(accum_emotions)
            db.commit()

            # Re-derive the Tuckman distribution from the entire accum_emotions
            entire_dist = self.stage_mapper.get_stage_distribution_from_entire_emotions(accum_emotions)
            member.save_accum_distrib(entire_dist)

            # (Optional) Finalize the stage if user has enough lines
            member.num_lines += 1
            db.commit()

            # Ephemeral lines track
            key_for_ephemeral = (team_name, member_name)
            if key_for_ephemeral not in self.lines_since_final_stage:
                self.lines_since_final_stage[key_for_ephemeral] = 0
            self.lines_since_final_stage[key_for_ephemeral] += 1

            # If user has >=3 lines, possibly finalize the stage
            if member.num_lines >= 3:
                # Find the highest stage in entire_dist
                best_sum = 0.0
                best_stage = None
                for s, v in entire_dist.items():
                    if v > best_sum:
                        best_sum = v
                        best_stage = s
                if best_sum > 0.5:
                    member.current_stage = best_stage
                    db.commit()
                    if self.lines_since_final_stage[key_for_ephemeral] >= 3:
                        # Generate personal feedback
                        personal_feedback = self.stage_mapper.get_personal_feedback(db, member.id, best_stage)
                        member.personal_feedback = personal_feedback
                        db.commit()

                        # Generate team feedback
                        team_feedback = self.stage_mapper.get_team_feedback(db, team.id, best_stage)
                        team.feedback = team_feedback
                        db.commit()

                        final_stage = best_stage
                        self.lines_since_final_stage[key_for_ephemeral] = 0

        # Recompute the entire team's stage
        self._compute_team_stage(db, team)

        if mode == "conversation":
            # Build conversation string for prompt, loading every message this member had (only the messages of this member, not taking into account his team members)
            all_msgs = db.query(Message).join(Member).filter(Member.id == member.id).all()
            all_msgs.sort(key=lambda x: x.id)

            lines_for_prompt = []
            for msg in all_msgs:
                if msg.role.lower() == "assistant":
                    lines_for_prompt.append(f"Assistant: {msg.text}")
                else:
                    lines_for_prompt.append(f"User ({msg.member.name}): {msg.text}")
            conversation_str = "\n".join(lines_for_prompt)

            # Generate final LLaMA answer
            bot_response = self._generate_response(conversation_str, text)
            assistant_msg = Message(
                member_id=member.id,
                role="Assistant",
                text=bot_response,
                detected_emotion="(Top-5 used)" if is_valuable else "(Skipped)",
                stage_at_time=final_stage if final_stage else "Uncertain"
            )
            db.add(assistant_msg)
            db.commit()

            # Return 7 items to match main.py's 7-value unpack
            return (
                bot_response,
                final_stage,
                team_feedback,
                accum_dist,
                last_emotion_dist,
                accum_emotions,
                personal_feedback
            )
        else:
            # In analysis mode, skip generating responses
            return (
                None,  # bot_response not needed
                final_stage,
                team_feedback,
                accum_dist,
                last_emotion_dist,
                accum_emotions,
                personal_feedback
            )

    def analyze_conversation_db(self, db, team_name: str, chat_log: str):
        """
        Processes and analyzes a conversation from a chat log.
        - Extracts members and messages.
        - Updates stages and emotions for each member.
        - Returns the overall team stage, feedback, and team distribution.
        """
        members = self._process_chat_log(db, team_name, chat_log)
        final_stage = None
        feedback = None
        distribution = {}

        for member_name in members:
            # Retrieve or create team and member
            team = self._load_team(db, team_name)
            member = self._load_member(db, team, member_name)

            # Retrieve all messages for this member
            messages = db.query(Message).filter(Message.member_id == member.id).all()
            for message in messages:
                _, concluded_stage, concluded_feedback, _, _, _, _ = self.process_line(
                    db, team_name, member_name, message.text, mode="analysis"
                )
                # Update final_stage and feedback if found
                if concluded_stage:
                    final_stage = concluded_stage
                    feedback = concluded_feedback

        # Calculate team distribution after processing all members
        team = self._load_team(db, team_name)
        distribution = team.load_team_distribution()

        # Return the final stage, feedback, and distribution
        return final_stage, feedback, distribution

    def reset_team(self, db, team_name: str):
        """
        Resets the team's stage and clears all associated member data.
        """
        team = db.query(Team).filter(Team.name == team_name).first()
        if team:
            team.current_stage = "Uncertain"
            for member in team.members:
                member.current_stage = "Uncertain"
                member.save_accum_distrib({})
                member.num_lines = 0
                member.save_accum_emotions({})
                db.query(Message).filter(Message.member_id == member.id).delete()
                db.commit()
            db.commit()

        keys_to_delete = []
        for (t_name, m_name) in self.lines_since_final_stage:
            if t_name == team_name:
                keys_to_delete.append((t_name, m_name))
        for k in keys_to_delete:
            del self.lines_since_final_stage[k]
