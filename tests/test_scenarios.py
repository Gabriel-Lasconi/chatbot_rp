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
                "team_name": "TeamAlpha",
                "member_name": "UserA",
                "expected_stage": "Forming",
                "lines": [
                    {
                        "text": "I love how fresh this all feels. Working with brand new faces is exciting.",
                        "expected_emotions": ["excitement"]
                    },
                    {
                        "text": "I can’t help wondering how we’ll coordinate; there’s so much we haven’t decided.",
                        "expected_emotions": ["curiosity"]
                    },
                    {
                        "text": "We should figure out how to handle tasks soon. I’m a bit unsure who leads, but let’s see.",
                        "expected_emotions": ["insecurity", "nervousness"]
                    },
                    {
                        "text": "Still, I’m genuinely looking forward to seeing everyone’s strengths.",
                        "expected_emotions": ["anticipation"]
                    },
                    {
                        "text": "We don’t know each other well yet, but the vibe so far is positive.",
                        "expected_emotions": ["hope"]
                    },
                    {
                        "text": "I’ve never done a project in such a large group. It’s a bit nerve-racking.",
                        "expected_emotions": ["nervousness"]
                    },
                    {
                        "text": "Same. The framework is new to me, so I’m excited and cautious at once.",
                        "expected_emotions": ["excitement", "cautious optimism"]
                    },
                    {
                        "text": "Let’s have a kickoff meeting tomorrow, break the ice, and start brainstorming.",
                        "expected_emotions": ["enthusiasm"]
                    },
                    {
                        "text": "Yes, I want to hear everyone’s background. I might be uncertain, but I’m ready to learn.",
                        "expected_emotions": ["uncertainty"]
                    },
                    {
                        "text": "Great! I’m pumped to see how each of us fits in.",
                        "expected_emotions": ["excitement"]
                    }
                ]
            },
            {
                "team_name": "TeamBeta",
                "member_name": "UserB",
                "expected_stage": "Storming",
                "lines": [
                    {
                        "text": "I hate to say it, but I'm irritated we keep overlapping tasks.",
                        "expected_emotions": ["frustration", "anger"]
                    },
                    {
                        "text": "We promised to plan better, but I see no real structure. It’s chaos.",
                        "expected_emotions": ["tension", "disappointment"]
                    },
                    {
                        "text": "I spent hours redoing code that someone changed behind my back. I’m upset.",
                        "expected_emotions": ["resentment"]
                    },
                    {
                        "text": "I’m worried we won’t meet the milestone if we keep snapping at each other.",
                        "expected_emotions": ["fear of conflict"]
                    },
                    {
                        "text": "It’s messing with the schedule. I feel no one’s truly listening.",
                        "expected_emotions": ["disappointment"]
                    },
                    {
                        "text": "The environment is edgy. Frankly, I dread the next group call.",
                        "expected_emotions": ["hostility", "discouragement"]
                    },
                    {
                        "text": "We have to fix this. Right now it’s just blame and negativity.",
                        "expected_emotions": ["conflict"]
                    },
                    {
                        "text": "It feels unfair how tasks get assigned. I’m stuck with the tedious parts alone.",
                        "expected_emotions": ["unfairness", "anger"]
                    },
                    {
                        "text": "I admit I’ve been defensive, but we need a calmer approach or we’ll fail.",
                        "expected_emotions": ["defensiveness"]
                    },
                    {
                        "text": "Agreed. Let’s get a mediator or something, because we can’t go on like this.",
                        "expected_emotions": ["frustration", "conflict"]
                    }
                ]
            },
            {
                "team_name": "TeamGamma",
                "member_name": "UserC",
                "expected_stage": "Norming",
                "lines": [
                    {
                        "text": "After all the earlier chaos, I can finally say I’m calmer. It’s easier to talk now.",
                        "expected_emotions": ["calm", "relief from resolved conflict"]
                    },
                    {
                        "text": "Yeah, that meltdown led us to define clearer roles, ironically.",
                        "expected_emotions": ["trust", "renewed hope"]
                    },
                    {
                        "text": "I’m comfortable asking for help now. Everyone seems open, which is great.",
                        "expected_emotions": ["empathy", "acceptance of roles"]
                    },
                    {
                        "text": "I love how the mood’s so peaceful compared to before.",
                        "expected_emotions": ["serenity"]
                    },
                    {
                        "text": "We overcame conflict, so I see genuine unity emerging.",
                        "expected_emotions": ["unity"]
                    },
                    {
                        "text": "I appreciate how we consult each other. That fosters strong commitment.",
                        "expected_emotions": ["commitment"]
                    },
                    {
                        "text": "The environment feels supportive. I’d call it real camaraderie now.",
                        "expected_emotions": ["camaraderie"]
                    },
                    {
                        "text": "I’m definitely trusting the group. Even small disagreements feel constructive.",
                        "expected_emotions": ["trust"]
                    },
                    {
                        "text": "Yes, it’s a relief. I see continuous improvement in how we handle tasks.",
                        "expected_emotions": ["relief from resolved conflict", "sense of growth"]
                    },
                    {
                        "text": "We should keep this synergy going. Let’s finalize everyone’s role clearly.",
                        "expected_emotions": ["feel of cohesion"]
                    }
                ]
            },
            {
                "team_name": "TeamDelta",
                "member_name": "UserD",
                "expected_stage": "Performing",
                "lines": [
                    {
                        "text": "We smashed that sprint backlog. Everything was done way ahead of time.",
                        "expected_emotions": ["confidence in team", "satisfaction with outcomes"]
                    },
                    {
                        "text": "I barely had to ask for help—everyone just stepped in. That’s real synergy.",
                        "expected_emotions": ["synergy"]
                    },
                    {
                        "text": "It’s so satisfying to watch tasks vanish quickly. I feel unstoppable.",
                        "expected_emotions": ["enthusiasm about goals", "satisfaction with outcomes"]
                    },
                    {
                        "text": "We have a rhythm I’d call flow. No wasted time, no friction.",
                        "expected_emotions": ["flow"]
                    },
                    {
                        "text": "I appreciate how each of us is proactive. It’s pure mutual respect.",
                        "expected_emotions": ["mutual respect"]
                    },
                    {
                        "text": "I’m proud of how we handle new challenges instantly. Feels like big confidence.",
                        "expected_emotions": ["self-confidence", "pride in work"]
                    },
                    {
                        "text": "We soared past initial targets. I'm excited to finalize advanced features.",
                        "expected_emotions": ["enthusiasm about goals"]
                    },
                    {
                        "text": "Yes, the sense of accomplishment is massive. Let’s keep pushing forward.",
                        "expected_emotions": ["accomplishment"]
                    },
                    {
                        "text": "A quick retrospective might help us optimize even more.",
                        "expected_emotions": ["confidence in team"]
                    },
                    {
                        "text": "Agreed. The synergy is real, and the outcomes are top-notch.",
                        "expected_emotions": ["synergy", "satisfaction with outcomes"]
                    }
                ]
            },
            {
                "team_name": "TeamEpsilon",
                "member_name": "UserE",
                "expected_stage": "Adjourning",
                "lines": [
                    {
                        "text": "We’re basically finished. I have a bittersweet feeling we'll disband soon.",
                        "expected_emotions": ["sense of loss"]
                    },
                    {
                        "text": "I'm glad we succeeded, but there's a real sadness about closure.",
                        "expected_emotions": ["sadness about closure"]
                    },
                    {
                        "text": "Looking back at the start makes me nostalgic for the group.",
                        "expected_emotions": ["nostalgia for the group"]
                    },
                    {
                        "text": "Odd not having daily calls soon, but I'm excited for what's next too.",
                        "expected_emotions": ["enthusiasm for the future", "uncertainty about next steps"]
                    },
                    {
                        "text": "I guess it's normal. Let's do a final retrospective tomorrow.",
                        "expected_emotions": ["reflection on achievements"]
                    },
                    {
                        "text": "Part of me is relieved it's over, but I'll miss it. Feels like closure.",
                        "expected_emotions": ["relief from completion", "closure"]
                    },
                    {
                        "text": "There's some emptiness, but also grateful for all we learned.",
                        "expected_emotions": ["emptiness after disbandment", "thankfulness for the experience"]
                    },
                    {
                        "text": "We overcame so much. I'm proud, but I sense a loss not continuing together.",
                        "expected_emotions": ["sense of loss"]
                    },
                    {
                        "text": "I hope we keep in touch. Maybe a new project will reunite us someday.",
                        "expected_emotions": ["enthusiasm for the future"]
                    },
                    {
                        "text": "Yes. I'll remember this journey fondly. Let’s officially wrap up.",
                        "expected_emotions": ["closure", "nostalgia for the group"]
                    }
                ]
            }
        ]

        # We'll store scenario-by-scenario results in self.results
        for scenario in scenarios:
            team_name = scenario["team_name"]
            member_name = scenario["member_name"]
            expected_stage = scenario["expected_stage"]
            lines_data = scenario["lines"]

            # Convert the lines to raw text
            text_lines = [d["text"] for d in lines_data]

            # 1) Analyze entire conversation with analyze_conversation_db
            final_stage, feedback, accum_dist = self.chatbot.analyze_conversation_db(
                self.db, team_name, member_name, text_lines
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
                ) = self.chatbot.process_line(self.db, team_name, member_name, text_line)

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
        self.create_excel_summary(self.results, "tuckman_scenarios_results.xlsx")

    def create_excel_summary(self, results, filename):
        df = pd.DataFrame(results)
        df.to_excel(filename, index=False)
        print(f"Excel results saved to {filename}")

    @classmethod
    def tearDownClass(cls):
        # If you want to close DB or something
        pass


if __name__ == "__main__":
    unittest.main()
