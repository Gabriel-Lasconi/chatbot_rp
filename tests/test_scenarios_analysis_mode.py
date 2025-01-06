# tests/test_scenarios_analysis_mode.py

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, Team, Message
from app.chatbot_generative import ChatbotGenerative

class TestChatbotAnalysisMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up an in-memory SQLite database just for this test class,
        so each scenario can use the analysis mode with a real DB session.
        """
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        SessionLocal = sessionmaker(bind=cls.engine)
        Base.metadata.create_all(cls.engine)
        cls.db = SessionLocal()

        cls.chatbot = ChatbotGenerative()

    @classmethod
    def tearDownClass(cls):
        """
        Drop all tables and dispose of the engine after tests are done.
        """
        cls.db.close()
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def tearDown(self):
        """
        After each test, we might want to remove any leftover data
        so that subsequent tests start with a clean slate.
        """
        self.db.query(Message).delete()
        self.db.query(Team).delete()
        self.db.commit()

    def test_forming_scenario_analysis(self):
        """
        Scenario A: A forming-like environment (TeamBeta).
        We feed the lines in bulk to analyze_conversation_db,
        using synonyms for excitement and curiosity, and extra lines.
        """
        lines = [
            "Alice: Hello everyone! I’m exhilarated to join this project!",
            "Bob: I’m a bit antsy about meeting new collaborators, but still optimistic.",
            "Cara: I’m unsure about the overall objectives. Does anyone know if we've set a target deadline?",
            "Dan: I'm excited but slightly worried that we don't have distinct roles yet.",
            "Alice: I'd love to clarify responsibilities. Maybe I can handle UI design?",
            "Bob: Great idea. I'm eager to see how we can coordinate effectively."
        ]

        final_stage, feedback = self.chatbot.analyze_conversation_db(self.db, "TeamBeta", lines)
        print("\n[Forming Scenario Analysis - TeamBeta]")
        print(f"Final Stage: {final_stage}")
        print(f"Feedback: {feedback}")

    def test_storming_scenario_analysis(self):
        """
        Scenario B: A storming-like environment (TeamGamma).
        Uses synonyms for frustration/conflict plus extra lines for tension.
        """
        lines = [
            "Erin: I'm irritated that we STILL don't have a well-defined plan!",
            "Felix: The friction here is growing. Why didn't we map tasks earlier?",
            "Gina: I'm on edge whenever people bring up deadlines...",
            "Henry: I'm doubtful we can complete this on time.",
            "Felix: We need to stop bickering and actually solve the workload distribution.",
            "Erin: Could we at least establish who owns each component? This stress is too high!",
            "Gina: Exactly. The indefinite roles are causing unnecessary hostility."
        ]

        final_stage, feedback = self.chatbot.analyze_conversation_db(self.db, "TeamGamma", lines)
        print("\n[Storming Scenario Analysis - TeamGamma]")
        print(f"Final Stage: {final_stage}")
        print(f"Feedback: {feedback}")

    def test_norming_scenario_analysis(self):
        """
        Scenario C: A norming environment (TeamDelta).
        Focus on relief, acceptance, cooperation. Added synonyms and extra lines.
        """
        lines = [
            "Iris: I'm relieved we assigned tasks. It soothes my nerves to have structure!",
            "Jack: Indeed, I accept everyone's input now; synergy is improving.",
            "Kara: I'm grateful we overcame earlier friction. I sense better rapport.",
            "Luke: There's a real sense of mutual trust forming here.",
            "Iris: Yes, the negativity is gone. This unity is a major boost.",
            "Jack: Let's keep reinforcing our cohesion, so we progress smoothly."
        ]

        final_stage, feedback = self.chatbot.analyze_conversation_db(self.db, "TeamDelta", lines)
        print("\n[Norming Scenario Analysis - TeamDelta]")
        print(f"Final Stage: {final_stage}")
        print(f"Feedback: {feedback}")

    def test_performing_transition_analysis(self):
        """
        Scenario D: Transition from Norming to Performing (TeamEpsilon).
        We add synonyms for pride, accomplishment, and strong confidence.
        """
        lines = [
            "Mia: I'm so proud of how far we've come. Our synergy is amazing now.",
            "Nate: Absolutely. I'm confident we can surpass our initial targets!",
            "Olivia: The sense of achievement is huge, and I'm thrilled with our progress.",
            "Paul: Let’s finalize the last milestone. I'm certain we can do even better than planned.",
            "Nate: Good idea—pushing ourselves further is exciting!"
        ]

        final_stage, feedback = self.chatbot.analyze_conversation_db(self.db, "TeamEpsilon", lines)
        print("\n[Norming to Performing Transition Analysis - TeamEpsilon]")
        print(f"Final Stage: {final_stage}")
        print(f"Feedback: {feedback}")

    def test_adjourning_scenario_analysis(self):
        """
        Scenario E: An adjourning environment (TeamZeta).
        We incorporate synonyms for nostalgia, closure, reflection, etc.
        """
        lines = [
            "Quinn: I'm sentimental realizing we’re almost done with this project.",
            "Riley: I feel a bittersweet mix of pride and sadness—so much accomplished!",
            "Sam: It's definitely closure time. Maybe we should hold a final retrospective.",
            "Tina: I'd love to reflect on our journey. Let’s record everything we learned.",
            "Quinn: For sure. This sense of finality is powerful, but I'm grateful for our achievements!",
            "Sam: Yes, let's wrap up properly and celebrate the last steps."
        ]

        final_stage, feedback = self.chatbot.analyze_conversation_db(self.db, "TeamZeta", lines)
        print("\n[Adjourning Scenario Analysis - TeamZeta]")
        print(f"Final Stage: {final_stage}")
        print(f"Feedback: {feedback}")
