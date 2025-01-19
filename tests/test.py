import unittest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.chatbot_generative import ChatbotGenerative
from app.db import Base, Team, Message



# Suppose you have these imports from your own code:
# from app.main import chatbot, get_db
# or from app.main import analyze_conversation_db, reset_team
# We'll assume we can do: chatbot.analyze_conversation_db(...)
# and chatbot.process_line(...)

class TuckmanScenarioTest(unittest.TestCase):
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


        # This list will store scenario-by-scenario results, which we will dump to Excel
        cls.results = []

    def test_scenarios(self):
        """
        A single test method that iterates over multiple synthetic Tuckman stage scenarios.
        Each scenario has ~10 lines with more natural expressions,
        an expected final stage, and a manual list of expected emotions per line.
        """

        scenarios = [
            {
                "team_name": "TeamForming",
                "expected_stage": "Forming",
                "lines": [
                    {
                        "text": "Bob: I love how fresh this all feels. Working with brand new faces is exciting.",
                        "expected_emotions": ["excitement"]
                    },
                    {
                        "text": "Alice: I can’t help wondering how we’ll coordinate; there’s so much we haven’t decided.",
                        "expected_emotions": ["curiosity"]
                    },
                    {
                        "text": "Bob: We should figure out how to handle tasks soon. I’m a bit unsure who leads, but let’s see.",
                        "expected_emotions": ["insecurity", "nervousness"]
                    },
                    {
                        "text": "Charlie: Still, I’m genuinely looking forward to seeing everyone’s strengths.",
                        "expected_emotions": ["anticipation"]
                    },
                ]
            }
        ]

        # We'll store scenario-by-scenario results in self.results
        for scenario in scenarios:
            team_name = scenario["team_name"]
            expected_stage = scenario["expected_stage"]
            lines_data = scenario["lines"]

            # Convert the lines to raw text
            text_lines = [d["text"] for d in lines_data]

            # 1) Analyze entire conversation with analyze_conversation_db
            final_stage, feedback, accum_dist = self.chatbot.analyze_conversation_db(
                self.db, team_name, text_lines
            )

            # Stage correctness
            stage_correct = (final_stage == expected_stage)

            # 2) Evaluate emotion accuracy line-by-line
            # We'll call process_line for each line to get last_emotion_dist
            line_correct_count = 0
            total_lines = len(lines_data)
            for line_item in lines_data:
                text_line = line_item["text"]
                expected_emos = line_item["expected_emotions"]  # list

                # process a single line
                (
                    bot_msg,
                    concluded_stage,
                    concluded_feedback,
                    accum_dist_line,
                    last_emotion_dist_line,
                    accum_emotions_line,
                    personal_feedback_line
                ) = self.chatbot.process_line(self.db, team_name, "X", text_line)

                # Build top-5 from last_emotion_dist_line
                # last_emotion_dist_line is presumably { "emotion_label": confidence, ... }
                top5_emos = sorted(
                    last_emotion_dist_line.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                top5_labels = [t[0].lower().strip() for t in top5_emos]

                # If any of the expected emos is found => correct line
                correct_line = False
                for e_emo in expected_emos:
                    if e_emo.lower().strip() in top5_labels:
                        correct_line = True
                        break
                if correct_line:
                    line_correct_count += 1

            emotion_accuracy = (line_correct_count / total_lines) * 100.0

            scenario_result = {
                "team_name": team_name,
                "lines": total_lines,
                "manual_stage": expected_stage,
                "chatbot_stage": final_stage if final_stage else "Uncertain",
                "stage_correct": "Yes" if stage_correct else "No",
                "emotion_correct_count": line_correct_count,
                "emotion_total_lines": total_lines,
                "emotion_accuracy_percent": round(emotion_accuracy, 1)
            }
            self.results.append(scenario_result)

        # 3) Save results to Excel
        self.create_excel_summary(self.results, "tuckman_scenarios_results4.xlsx")

    def create_excel_summary(self, results, filename):
        df = pd.DataFrame(results)
        df.to_excel(filename, index=False)
        print(f"Excel results saved to {filename}")

    # @classmethod
    # def tearDownClass(cls):
    #     # If you want to close DB or something
    #     pass


if __name__ == "__main__":
    unittest.main()
