import unittest
from unittest.mock import MagicMock

from app.chatbot_generative import ChatbotGenerative


class TestClassifyMessageRelevance(unittest.TestCase):
    def setUp(self):
        self.mock_model = MagicMock()
        self.chatbot = ChatbotGenerative()
        self.chatbot.model = self.mock_model

    def test_relevant_messages(self):
        self.mock_model.invoke.side_effect = lambda input: "Valuable"

        relevant_inputs = [
            "I feel frustrated because nobody listens to my ideas.",
            "There seems to be tension between team members lately.",
            "Trust within the team has improved significantly.",
            "We are finally achieving cohesion and understanding roles.",
            "I am proud of the progress we’ve made as a team."
        ]

        for message in relevant_inputs:
            with self.subTest(message=message):
                self.assertTrue(self.chatbot._classify_message_relevance(message))

    def test_irrelevant_messages(self):
        self.mock_model.invoke.side_effect = lambda input: "Skip"

        irrelevant_inputs = [
            "Hello!",
            "Good morning, how are you?",
            "Let’s start the meeting.",
            "What’s the agenda for today?",
            "See you tomorrow!"
        ]

        for message in irrelevant_inputs:
            with self.subTest(message=message):
                self.assertFalse(self.chatbot._classify_message_relevance(message))

    def test_mixed_inputs(self):
        def mock_side_effect(input):
            if "frustrated" in input or "tension" in input or "proud" in input:
                return "Valuable"
            else:
                return "Skip"

        self.mock_model.invoke.side_effect = mock_side_effect

        mixed_inputs = [
            ("I feel frustrated because nobody listens to my ideas.", True),
            ("Hello!", False),
            ("There seems to be tension between team members lately.", True),
            ("Good morning, how are you?", False),
            ("I am proud of the progress we’ve made as a team.", True),
        ]

        for message, expected in mixed_inputs:
            with self.subTest(message=message):
                self.assertEqual(self.chatbot._classify_message_relevance(message), expected)

if __name__ == "__main__":
    unittest.main()
