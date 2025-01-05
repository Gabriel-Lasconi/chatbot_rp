# tests/test_scenarios_analysis_mode.py

import unittest
from app.chatbot_generative import ChatbotGenerative

class TestChatbotAnalysisMode(unittest.TestCase):
    def setUp(self):
        """
        Initialize the ChatbotGenerative instance.
        """
        self.chatbot = ChatbotGenerative()

    def tearDown(self):
        """
        Reset after each test so each scenario starts fresh.
        """
        self.chatbot.reset_conversation()

    def test_forming_scenario_analysis(self):
        """
        Scenario A: A forming-like environment where team members express excitement and mild anxiety.
        We feed the lines in bulk to analyze_conversation.
        """
        lines = [
            "Alice: Hello everyone! I’m super excited to be part of this team!",
            "Bob: I’m eager to get started, but a bit anxious about responsibilities.",
            "Cara: I’m curious about our overall goals. Does anyone know if we have a clear timeline?",
            "Dan: I’m enthusiastic, but also unsure about the next steps.",
            "Alice: Just to confirm, I’ll handle the design aspects, right?",
        ]

        final_stage, feedback = self.chatbot.analyze_conversation(lines)
        print("\n[Forming Scenario Analysis]")
        print(f"Final Stage: {final_stage}")
        print(f"Feedback: {feedback}\n")

    def test_storming_scenario_analysis(self):
        """
        Scenario B: A storming-like environment with frustration and conflict.
        The chatbot should identify Storming after enough lines.
        """
        lines = [
            "Erin: I’m frustrated that we STILL don’t have a final schedule!",
            "Felix: This tension is getting out of hand. Why didn’t anyone step up?",
            "Gina: I keep feeling defensive whenever tasks are brought up...",
            "Henry: I'm uncertain if we can fix this in time.",
            "Felix: I want us to stop fighting and focus on solutions.",
            "Erin: Let’s at least figure out who’s responsible for the next steps to ease frustration."
        ]

        final_stage, feedback = self.chatbot.analyze_conversation(lines)
        print("\n[Storming Scenario Analysis]")
        print(f"Final Stage: {final_stage}")
        print(f"Feedback: {feedback}\n")

    def test_norming_scenario_analysis(self):
        """
        Scenario C: A norming environment with relief, trust, and acceptance.
        """
        lines = [
            "Iris: I’m relieved we finally assigned tasks. Thanks for clarifying the timeline!",
            "Jack: I trust we can be more cohesive now. I’m open to feedback from everyone.",
            "Kara: This acceptance is refreshing. Camaraderie seems higher than ever!",
            "Luke: I’m optimistic about hitting our main deadlines.",
            "Jack: Let’s keep reinforcing this positive momentum."
        ]

        final_stage, feedback = self.chatbot.analyze_conversation(lines)
        print("\n[Norming Scenario Analysis]")
        print(f"Final Stage: {final_stage}")
        print(f"Feedback: {feedback}\n")

    def test_performing_transition_analysis(self):
        """
        Scenario D: Transition from Norming to Performing, showing pride and strong accomplishment focus.
        """
        lines = [
            "Mia: Great that we overcame earlier issues. Feeling more aligned now.",
            "Nate: I accept everyone’s feedback. Let’s keep cooperation strong.",
            "Olivia: I’m proud of how we overcame tensions. Our accomplishments are growing.",
            "Paul: Let’s finalize the next milestone. I’m confident we can exceed expectations!"
        ]

        final_stage, feedback = self.chatbot.analyze_conversation(lines)
        print("\n[Norming to Performing Transition Analysis]")
        print(f"Final Stage: {final_stage}")
        print(f"Feedback: {feedback}\n")

    def test_adjourning_scenario_analysis(self):
        """
        Scenario E: An adjourning environment with nostalgia, reflection, and closure.
        """
        lines = [
            "Quinn: Feeling nostalgic knowing we’re wrapping up soon.",
            "Riley: I’m both sad and proud. So much accomplished.",
            "Sam: Definitely a sense of closure. We should celebrate!",
            "Tina: Let’s document everything we learned before we disband.",
            "Quinn: Reflection is key. Our achievements deserve a final shout-out."
        ]

        final_stage, feedback = self.chatbot.analyze_conversation(lines)
        print("\n[Adjourning Scenario Analysis]")
        print(f"Final Stage: {final_stage}")
        print(f"Feedback: {feedback}\n")
