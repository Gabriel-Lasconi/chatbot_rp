# chatbot_generative.py

import re

from langchain_ollama import OllamaLLM
from app.emotion_analysis import EmotionDetector
from app.stage_mapping import StageMapper
from app.db import Team, Member, Message

class ChatbotGenerative:
    def __init__(self):
        """
        Initializes the ChatbotGenerative with necessary components like the language model,
        emotion detector, and stage mapper. Also sets up system instructions and tracking for stages.
        """
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

        # Tracks the number of lines since the final stage was set for each team-member
        self.lines_since_final_stage = {}

    # ========================================================
    #   STAGE MAPPER PROPERTY
    # ========================================================

    @property
    def stage_mapper(self):
        return self._stage_mapper

    @stage_mapper.setter
    def stage_mapper(self, value):
        self._stage_mapper = value

    # ========================================================
    #   TEAM AND MEMBER LOADING FUNCTIONS
    # ========================================================

    def _load_team(self, db, team_name: str):
        """
        Retrieves or creates a team in the database.

        Args:
            db (Session): Database session.
            team_name (str): Name of the team.

        Returns:
            Team: The team instance.
        """
        team = db.query(Team).filter(Team.name == team_name).first()
        if not team:
            team = Team(name=team_name, current_stage="Uncertain")
            db.add(team)
            db.commit()
            db.refresh(team)
        return team

    def _load_member(self, db, team, member_name: str):
        """
        Retrieves or creates a member in the database.

        Args:
            db (Session): Database session.
            team (Team): The team instance.
            member_name (str): Name of the member.

        Returns:
            Member: The member instance.
        """
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

    # ========================================================
    #   CHAT LOG PROCESSING FUNCTIONS
    # ========================================================

    def _normalize_member_names(self, members):
        """
        Normalizes member names by removing emojis and trimming whitespace.
        This helps in preventing duplicates caused by formatting differences.

        Args:
            members (list): List of member names.

        Returns:
            list: List of normalized member names.
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
        Extracts members and their messages from the provided chat log.
        Handles both formats:
        1. [timestamp] Name: message
        2. Name: message

        Args:
            chat_log (str): The raw chat log text.

        Returns:
            dict: A mapping of member names to their list of messages.
        """
        member_message_map = {}

        cleaned_chat_log = re.sub(r"[\u200e]", "", chat_log)

        pattern = re.compile(r"(?:\[(.*?)\] )?(.*?): (.*)")

        for line in cleaned_chat_log.splitlines():
            match = pattern.match(line)
            if match:
                _, name, message = match.groups()
                if name:
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

        Args:
            db (Session): Database session.
            team_name (str): Name of the team.
            chat_log (str or list): The raw chat log text or list of messages.

        Returns:
            list: List of member names extracted from the chat log.
        """
        team = self._load_team(db, team_name)

        if isinstance(chat_log, list):
            chat_log = "\n".join(chat_log)

        member_message_map = self._extract_members_and_messages(chat_log)

        for member_name, messages in member_message_map.items():
            member = self._load_member(db, team, member_name)

            for message in messages:
                user_msg = Message(member_id=member.id, role="User", text=message)
                db.add(user_msg)
            db.commit()

        return member_message_map.keys()

    # ========================================================
    #   PROMPT BUILDING FUNCTIONS
    # ========================================================

    def _build_prompt(self, conversation_str: str, user_message: str) -> str:
        """
        Builds the prompt for the language model by combining system instructions,
        existing conversation, and the new user message.

        Args:
            conversation_str (str): The existing conversation history.
            user_message (str): The latest message from the user.

        Returns:
            str: The complete prompt for the language model.
        """
        prompt = (
            f"<<SYS>>\n{self.system_instructions}\n<</SYS>>\n\n"
            f"{conversation_str}\n"
            f"User: {user_message}\n"
            "Assistant:"
        )
        return prompt

    def _generate_response(self, conversation_str: str, user_message: str) -> str:
        """
        Generates a response from the language model based on the conversation and user message.

        Args:
            conversation_str (str): The existing conversation history.
            user_message (str): The latest message from the user.

        Returns:
            str: The generated response from the assistant.
        """
        prompt = self._build_prompt(conversation_str, user_message)
        response = self.model.invoke(input=prompt)
        return response.strip()

    # ========================================================
    #   MESSAGE RELEVANCE CLASSIFICATION
    # ========================================================

    def _classify_message_relevance(self, text: str) -> bool:
        """
        Classifies whether a user message is 'Valuable' or should be 'Skipped', if it does not have any emotional value.

        Args:
            text (str): The user message text.

        Returns:
            bool: True if the message is valuable, False otherwise.
        """
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

    # ========================================================
    #   TEAM STAGE COMPUTATION
    # ========================================================

    def _compute_team_stage(self, db, team):
        """
        After updating each member's accum_distrib, compute the 'combined' distribution
        for the entire team, then pick the stage with the highest value as the final team stage.

        Args:
            db (Session): Database session.
            team (Team): The team instance.
        """
        stage_names = ["Forming", "Storming", "Norming", "Performing", "Adjourning"]
        combined = {s: 0.0 for s in stage_names}
        num_members = 0

        for mem in team.members:
            dist = mem.load_accum_distrib()
            if dist:
                num_members += 1
                for stg, val in dist.items():
                    if stg in combined:
                        combined[stg] += val

        if num_members > 0:
            for stg in combined:
                combined[stg] /= num_members
        else:
            combined = {}

        team.save_team_distribution(combined)
        db.commit()

        if not combined or all(v == 0.0 for v in combined.values()):
            team.current_stage = "Uncertain"
            db.commit()
            return

        best_stage = max(combined, key=combined.get)
        best_val = combined[best_stage]

        team.current_stage = best_stage
        db.commit()

    # ========================================================
    #   MAIN PROCESSING FUNCTION
    # ========================================================

    def process_line(self, db, team_name: str, member_name: str, text: str, mode: str = "conversation"):
        """
        Processes a single line of conversation, either in conversation or analysis mode.

        Args:
            db (Session): Database session.
            team_name (str): Name of the team.
            member_name (str): Name of the member.
            text (str): The message text.
            mode (str): 'conversation' or 'analysis'. Determines whether to generate assistant responses.

        Returns:
            tuple: Contains bot_response, final_stage, team_feedback, accum_dist,
                   last_emotion_dist, accum_emotions, personal_feedback.
        """
        team = self._load_team(db, team_name)
        member = self._load_member(db, team, member_name)

        user_msg = Message(member_id=member.id, role="User", text=text)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        accum_dist = member.load_accum_distrib()
        accum_emotions = member.load_accum_emotions()
        final_stage = team.load_current_stage()
        team_feedback = team.load_feedback()
        personal_feedback = member.load_personal_feedback()

        if not accum_dist:
            accum_dist = {stg: 0.0 for stg in self.stage_mapper.stage_emotion_map.keys()}
        if not accum_emotions:
            accum_emotions = {}

        last_emotion_dist = {}

        is_valuable = self._classify_message_relevance(text)
        if is_valuable:
            emotion_results = self.emotion_detector.detect_emotion(text, top_n=5)
            top5_emotions = emotion_results["top_emotions"]

            dist_for_message = {emo["label"]: emo["score"] for emo in top5_emotions}
            user_msg.save_top_emotion_distribution(dist_for_message)
            db.commit()

            last_emotion_dist = dist_for_message

            for e_dict in top5_emotions:
                lbl = e_dict["label"]
                conf = e_dict["score"]
                accum_emotions[lbl] = accum_emotions.get(lbl, 0.0) + conf

            sum_emotions = sum(accum_emotions.values())
            if sum_emotions > 0.0:
                for e_lbl in accum_emotions:
                    accum_emotions[e_lbl] = accum_emotions[e_lbl] / sum_emotions

            member.save_accum_emotions(accum_emotions)
            db.commit()

            entire_dist = self.stage_mapper.get_stage_distribution_from_entire_emotions(accum_emotions)
            member.save_accum_distrib(entire_dist)

            member.num_lines += 1
            db.commit()

            key_for_ephemeral = (team_name, member_name)
            if key_for_ephemeral not in self.lines_since_final_stage:
                self.lines_since_final_stage[key_for_ephemeral] = 0
            self.lines_since_final_stage[key_for_ephemeral] += 1

            if member.num_lines >= 3:
                best_stage = max(entire_dist, key=entire_dist.get)
                best_val = entire_dist[best_stage]

                if best_val > 0.5:
                    member.current_stage = best_stage
                    db.commit()

                    if self.lines_since_final_stage[key_for_ephemeral] >= 3:
                        personal_feedback = self.stage_mapper.get_personal_feedback(db, member.id, best_stage)
                        member.personal_feedback = personal_feedback
                        db.commit()

                        team_feedback = self.stage_mapper.get_team_feedback(db, team.id, best_stage)
                        team.feedback = team_feedback
                        db.commit()

                        final_stage = best_stage
                        self.lines_since_final_stage[key_for_ephemeral] = 0

        self._compute_team_stage(db, team)

        if mode == "conversation":
            all_msgs = db.query(Message).join(Member).filter(Member.id == member.id).all()
            all_msgs.sort(key=lambda x: x.id)

            lines_for_prompt = []
            for msg in all_msgs:
                if msg.role.lower() == "assistant":
                    lines_for_prompt.append(f"Assistant: {msg.text}")
                else:
                    lines_for_prompt.append(f"User ({msg.member.name}): {msg.text}")
            conversation_str = "\n".join(lines_for_prompt)

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
            # In analysis mode, skip generating assistant responses
            return (
                None,
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

        Args:
            db (Session): Database session.
            team_name (str): Name of the team.
            chat_log (str): The raw chat log text.

        Returns:
            tuple: Contains final_stage, feedback, and distribution.
        """
        members = self._process_chat_log(db, team_name, chat_log)
        final_stage = None
        feedback = None
        distribution = {}

        for member_name in members:
            team = self._load_team(db, team_name)
            member = self._load_member(db, team, member_name)

            messages = db.query(Message).filter(Message.member_id == member.id).all()
            for message in messages:
                _, concluded_stage, concluded_feedback, _, _, _, _ = self.process_line(
                    db, team_name, member_name, message.text, mode="analysis"
                )
                if concluded_stage:
                    final_stage = concluded_stage
                    feedback = concluded_feedback

        team = self._load_team(db, team_name)
        distribution = team.load_team_distribution()

        return final_stage, feedback, distribution

    # ========================================================
    #   TEAM RESET FUNCTION
    # ========================================================

    def reset_team(self, db, team_name: str):
        """
        Resets the team's stage and clears all associated member data.

        Args:
            db (Session): Database session.
            team_name (str): Name of the team to reset.
        """
        team = db.query(Team).filter(Team.name == team_name).first()
        if team:
            team.current_stage = "Uncertain"
            team.feedback = ""
            for member in team.members:
                member.current_stage = "Uncertain"
                member.save_accum_distrib({})
                member.num_lines = 0
                member.save_accum_emotions({})
                member.personal_feedback = ""
                db.query(Message).filter(Message.member_id == member.id).delete()
                db.commit()
            db.commit()

        keys_to_delete = []
        for (t_name, m_name) in self.lines_since_final_stage:
            if t_name == team_name:
                keys_to_delete.append((t_name, m_name))
        for k in keys_to_delete:
            del self.lines_since_final_stage[k]
