import unittest
from app.emotion_analysis import EmotionDetector


class TestEmotionAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.emotion_detector = EmotionDetector()

    def test_emotion_detection_satisfaction(self):
        """
        Test that a satisfied emotion can be detected.
        """
        result = self.emotion_detector.detect_emotion("I am very happy with the team's progress!")
        self.assertIn("label", result)
        self.assertIn("score", result)
        self.assertEqual(result["label"], "satisfaction")

    def test_emotion_detection_negative(self):
        """
        Test that a negative sentiment is correctly classified.
        """
        result = self.emotion_detector.detect_emotion("There are so many conflicts in the team.")
        self.assertIn("label", result)
        self.assertIn("score", result)
        self.assertEqual(result["label"], "conflict")
        self.assertGreater(result["score"], 0.5)

    def test_emotion_detection_accomplishment(self):
        """
        Test that a accomplishment is correctly classified.
        """
        result = self.emotion_detector.detect_emotion("The team is achieving it's goals")
        self.assertIn("label", result)
        self.assertIn("score", result)
        self.assertEqual(result["label"], "accomplishment")

    # def test_emotion_detection_low_confidence(self):
    #     """
    #     Test that low-confidence emotions are handled correctly.
    #     """
    #     result = self.emotion_detector.detect_emotion("I'm not sure how the team is doing.")
    #     self.assertIn("label", result)
    #     self.assertIn("score", result)
    #     self.assertLess(result["score"], 0.5)  # Assuming low confidence for uncertain inputs

    def test_emotion_detection_with_unsupported_text(self):
        """
        Test that unsupported or ambiguous text is handled.
        """
        result = self.emotion_detector.detect_emotion("This is an ambiguous statement.")
        self.assertIn("label", result)
        self.assertIn("score", result)
        self.assertTrue(result["label"])  # Label should not be empty
        self.assertGreaterEqual(result["score"], 0.0)

    def test_emotion_classification_with_special_characters(self):
        """
        Test emotion detection for text containing special characters.
        """
        result = self.emotion_detector.detect_emotion("!!! Absolutely incredible job!!!")
        self.assertIn("label", result)
        self.assertIn("score", result)
        self.assertEqual(result["label"], "accomplishment")
        self.assertGreater(result["score"], 0.6)

    def test_emotion_classification_empty_string(self):
        """
        Test emotion detection for an empty string, it should be uncertain.
        """
        result = self.emotion_detector.detect_emotion("")
        self.assertEqual(result["label"], "uncertainty")
        self.assertEqual(result["score"], 1.0)

    def test_emotion_classification_whitespace(self):
        """
        Test emotion detection for a string with only whitespace it should be uncertain.
        """
        result = self.emotion_detector.detect_emotion("   ")
        self.assertEqual(result["label"], "uncertainty")
        self.assertEqual(result["score"], 1.0)


if __name__ == "__main__":
    unittest.main()
