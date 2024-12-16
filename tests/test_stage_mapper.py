import unittest
from app.stage_mapping import StageMapper

class TestStageMapper(unittest.TestCase):
    def setUp(self):
        """
        Set up the StageMapper instance for each test.
        """
        self.stage_mapper = StageMapper()

    def test_map_emotions_to_stage_single_stage(self):
        """
        Test mapping emotions that align to a single stage.
        """
        emotions_with_confidences = [
            ("eagerness", 0.7),
            ("curiosity", 0.6),
            ("anticipation", 0.5),
        ]
        result = self.stage_mapper.map_emotions_to_stage(emotions_with_confidences)
        self.assertEqual(result, "Forming")

    def test_map_emotions_to_stage_multiple_stages(self):
        """
        Test mapping emotions that align with multiple stages.
        """
        emotions_with_confidences = [
            ("trust", 0.6),  # Norming
            ("confidence", 0.4),  # Performing
            ("pride", 0.3),  # Performing
        ]
        result = self.stage_mapper.map_emotions_to_stage(emotions_with_confidences)
        self.assertEqual(result, "Performing")  # Norming has the highest cumulative score.

    def test_map_emotions_to_stage_no_matching_emotions(self):
        """
        Test when emotions do not match any stage.
        """
        emotions_with_confidences = [
            ("unknown_emotion1", 0.8),
            ("unknown_emotion2", 0.5),
        ]
        result = self.stage_mapper.map_emotions_to_stage(emotions_with_confidences)
        self.assertEqual(result, "Uncertain")

    def test_map_emotions_to_stage_empty_list(self):
        """
        Test when the input list is empty.
        """
        emotions_with_confidences = []
        result = self.stage_mapper.map_emotions_to_stage(emotions_with_confidences)
        self.assertEqual(result, "Uncertain")

    def test_map_emotions_to_stage_mixed_confidences(self):
        """
        Test when emotions align to different stages but one has higher confidence cumulatively.
        """
        emotions_with_confidences = [
            ("frustration", 0.3),  # Storming
            ("trust", 0.5),  # Norming
            ("cohesion", 0.4),  # Norming
            ("nostalgia", 0.2),  # Adjourning
        ]
        result = self.stage_mapper.map_emotions_to_stage(emotions_with_confidences)
        self.assertEqual(result, "Norming")  # Norming has the highest cumulative score.

    def test_get_feedback_for_valid_stage(self):
        """
        Test feedback generation for a valid stage.
        """
        stage = "Forming"
        feedback = self.stage_mapper.get_feedback_for_stage(stage)
        self.assertIsInstance(feedback, str)
        self.assertGreater(len(feedback), 0)  # Ensure non-empty feedback.

    def test_get_feedback_for_invalid_stage(self):
        """
        Test feedback generation for an invalid stage.
        """
        stage = "UnknownStage"
        feedback = self.stage_mapper.get_feedback_for_stage(stage)
        self.assertEqual(feedback, "No feedback available for this stage.")

    def test_get_feedback_with_llama_failure(self):
        """
        Test the feedback generation when LLaMA model fails (simulate exception).
        """
        self.stage_mapper.llama_model.invoke = lambda input: 1 / 0  # Simulate failure
        stage = "Forming"
        feedback = self.stage_mapper.get_feedback_for_stage(stage)
        self.assertEqual(feedback, "An error occurred while generating feedback. Please try again.")


if __name__ == "__main__":
    unittest.main()
