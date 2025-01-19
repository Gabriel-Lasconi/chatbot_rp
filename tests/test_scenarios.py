import unittest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.chatbot_generative import ChatbotGenerative
from app.db import Base, Team, Message

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
                    {
                        "text": "Alice: We don’t know each other well yet, but the vibe so far is positive.",
                        "expected_emotions": ["hope"]
                    },
                    {
                        "text": "Charlie: I’ve never done a project in such a large group. It’s a bit nerve-racking.",
                        "expected_emotions": ["nervousness"]
                    },
                    {
                        "text": "Bob: Same. The framework is new to me, so I’m excited and cautious at once.",
                        "expected_emotions": ["excitement", "cautious optimism"]
                    },
                    {
                        "text": "Alice: Let’s have a kickoff meeting tomorrow, break the ice, and start brainstorming.",
                        "expected_emotions": ["enthusiasm"]
                    },
                    {
                        "text": "Charlie: Yes, I want to hear everyone’s background. I might be uncertain, but I’m ready to learn.",
                        "expected_emotions": ["uncertainty"]
                    },
                    {
                        "text": "Bob: Great! I’m pumped to see how each of us fits in.",
                        "expected_emotions": ["excitement"]
                    },
                    {
                        "text": "Alice: I'm interested in understanding everyone's roles better. It'll help us collaborate smoothly.",
                        "expected_emotions": ["interest"]
                    },
                    {
                        "text": "Charlie: I have mild anxiety about meeting our deadlines, but I trust we'll manage.",
                        "expected_emotions": ["mild anxiety", "trust"]
                    },
                    {
                        "text": "Bob: It’s natural to feel a bit insecure in a new team, but I believe we can establish a strong foundation.",
                        "expected_emotions": ["insecurity", "trust"]
                    },
                    {
                        "text": "Alice: Let's take some time to introduce ourselves properly, so we can build trust from the start.",
                        "expected_emotions": ["trust"]
                    },
                    {
                        "text": "Charlie: I’m curious about how we’ll tackle challenges together. It’s exciting to think about.",
                        "expected_emotions": ["curiosity", "excitement"]
                    },
                    {
                        "text": "Bob: I feel hopeful that our diverse skills will complement each other and lead to success.",
                        "expected_emotions": ["hope"]
                    },
                    {
                        "text": "Alice: As we get to know each other, I think our coordination will improve significantly.",
                        "expected_emotions": ["hope"]
                    },
                    {
                        "text": "Charlie: I’m cautiously optimistic about our project. Let's keep communication open.",
                        "expected_emotions": ["cautious optimism"]
                    },
                    {
                        "text": "Bob: Overall, I’m excited to be part of this team and see what we can achieve together.",
                        "expected_emotions": ["excitement"]
                    },
                    {
                        "text": "Alice: Yes, let's embrace this opportunity and set ourselves up for a positive start.",
                        "expected_emotions": ["enthusiasm"]
                    }
                ]
            },
            {
                "team_name": "TeamStorming",
                "expected_stage": "Storming",
                "lines": [
                    {
                        "text": "Eve: I hate to say it, but I'm irritated we keep overlapping tasks.",
                        "expected_emotions": ["frustration", "anger"]
                    },
                    {
                        "text": "Frank: We promised to plan better, but I see no real structure. It’s chaos.",
                        "expected_emotions": ["tension", "disappointment"]
                    },
                    {
                        "text": "Eve: I spent hours redoing code that someone changed behind my back. I’m upset.",
                        "expected_emotions": ["resentment"]
                    },
                    {
                        "text": "Grace: I’m worried we won’t meet the milestone if we keep snapping at each other.",
                        "expected_emotions": ["fear of conflict"]
                    },
                    {
                        "text": "Frank: It’s messing with the schedule. I feel no one’s truly listening.",
                        "expected_emotions": ["disappointment"]
                    },
                    {
                        "text": "Eve: The environment is edgy. Frankly, I dread the next group call.",
                        "expected_emotions": ["hostility", "discouragement"]
                    },
                    {
                        "text": "Grace: We have to fix this. Right now it’s just blame and negativity.",
                        "expected_emotions": ["conflict"]
                    },
                    {
                        "text": "Frank: It feels unfair how tasks get assigned. I’m stuck with the tedious parts alone.",
                        "expected_emotions": ["unfairness", "anger"]
                    },
                    {
                        "text": "Eve: I admit I’ve been defensive, but we need a calmer approach or we’ll fail.",
                        "expected_emotions": ["defensiveness"]
                    },
                    {
                        "text": "Grace: Agreed. Let’s get a mediator or something, because we can’t go on like this.",
                        "expected_emotions": ["frustration", "conflict"]
                    },
                    {
                        "text": "Frank: I feel like my concerns are dismissed. It’s really discouraging.",
                        "expected_emotions": ["discouragement"]
                    },
                    {
                        "text": "Eve: Every time we discuss tasks, it turns into an argument. It’s exhausting.",
                        "expected_emotions": ["frustration", "tension"]
                    },
                    {
                        "text": "Grace: I sense that our lack of clear communication is causing a lot of friction.",
                        "expected_emotions": ["conflict"]
                    },
                    {
                        "text": "Frank: It’s unfair how some of us take on more work while others slack off.",
                        "expected_emotions": ["unfairness", "resentment"]
                    },
                    {
                        "text": "Eve: We need to establish better boundaries to prevent this chaos.",
                        "expected_emotions": ["frustration"]
                    },
                    {
                        "text": "Grace: I'm feeling overwhelmed with the constant disagreements. We need a solution.",
                        "expected_emotions": ["discouragement"]
                    },
                    {
                        "text": "Frank: I can’t keep handling the tedious tasks alone. It’s not sustainable.",
                        "expected_emotions": ["unfairness"]
                    },
                    {
                        "text": "Eve: I’m frustrated by the lack of progress. It’s like we’re stuck in a loop.",
                        "expected_emotions": ["frustration"]
                    },
                    {
                        "text": "Grace: Our meetings are counterproductive. We need to change our approach.",
                        "expected_emotions": ["frustration"]
                    },
                    {
                        "text": "Frank: If we don’t address these issues now, we’re doomed to fail.",
                        "expected_emotions": ["fear of conflict", "tension"]
                    }
                ]
            },
            {
                "team_name": "TeamNorming",
                "expected_stage": "Norming",
                "lines": [
                    {
                        "text": "Hank: After all the earlier chaos, I can finally say I’m calmer. It’s easier to talk now.",
                        "expected_emotions": ["calm", "relief from resolved conflict"]
                    },
                    {
                        "text": "Ivy: Yeah, that meltdown led us to define clearer roles, ironically.",
                        "expected_emotions": ["trust", "renewed hope"]
                    },
                    {
                        "text": "Jack: I’m comfortable asking for help now. Everyone seems open, which is great.",
                        "expected_emotions": ["empathy", "acceptance of roles"]
                    },
                    {
                        "text": "Hank: I love how the mood’s so peaceful compared to before.",
                        "expected_emotions": ["serenity"]
                    },
                    {
                        "text": "Ivy: We overcame conflict, so I see genuine unity emerging.",
                        "expected_emotions": ["unity"]
                    },
                    {
                        "text": "Jack: I appreciate how we consult each other. That fosters strong commitment.",
                        "expected_emotions": ["commitment"]
                    },
                    {
                        "text": "Hank: The environment feels supportive. I’d call it real camaraderie now.",
                        "expected_emotions": ["camaraderie"]
                    },
                    {
                        "text": "Ivy: I’m definitely trusting the group. Even small disagreements feel constructive.",
                        "expected_emotions": ["trust"]
                    },
                    {
                        "text": "Jack: Yes, it’s a relief. I see continuous improvement in how we handle tasks.",
                        "expected_emotions": ["relief from resolved conflict", "sense of growth"]
                    },
                    {
                        "text": "Hank: We should keep this synergy going. Let’s finalize everyone’s role clearly.",
                        "expected_emotions": ["feel of cohesion"]
                    },
                    {
                        "text": "Ivy: It feels like we all know what’s expected, which reduces confusion.",
                        "expected_emotions": ["trust", "acceptance of roles"]
                    },
                    {
                        "text": "Jack: Our mutual respect is evident in how we support each other’s ideas.",
                        "expected_emotions": ["empathy"]
                    },
                    {
                        "text": "Hank: I’m feeling a strong sense of unity within the team now.",
                        "expected_emotions": ["unity"]
                    },
                    {
                        "text": "Ivy: The commitment everyone shows really boosts our productivity.",
                        "expected_emotions": ["commitment", "satisfaction with outcomes"]
                    },
                    {
                        "text": "Jack: I'm calm knowing that we can handle any challenge that comes our way.",
                        "expected_emotions": ["calm"]
                    },
                    {
                        "text": "Hank: The camaraderie here makes working together enjoyable.",
                        "expected_emotions": ["camaraderie"]
                    },
                    {
                        "text": "Ivy: I trust our team completely. It’s empowering to know we have each other's backs.",
                        "expected_emotions": ["trust"]
                    },
                    {
                        "text": "Jack: Seeing our continuous improvement makes me feel proud of our progress.",
                        "expected_emotions": ["sense of growth", "pride in work"]
                    },
                    {
                        "text": "Hank: Our supportive environment encourages me to take initiative.",
                        "expected_emotions": ["empowerment"]
                    },
                    {
                        "text": "Ivy: I appreciate our open and honest communication. It really strengthens our team.",
                        "expected_emotions": ["trust"]
                    }
                ]
            },
            {
                "team_name": "TeamPerforming",
                "expected_stage": "Performing",
                "lines": [
                    {
                        "text": "Tom: We smashed that sprint backlog. Everything was done way ahead of time.",
                        "expected_emotions": ["confidence in team", "satisfaction with outcomes"]
                    },
                    {
                        "text": "Liam: I barely had to ask for help—everyone just stepped in. That’s real synergy.",
                        "expected_emotions": ["synergy"]
                    },
                    {
                        "text": "Sophia: It’s so satisfying to watch tasks vanish quickly. I feel unstoppable.",
                        "expected_emotions": ["enthusiasm about goals", "satisfaction with outcomes"]
                    },
                    {
                        "text": "Liam: We have a rhythm I’d call flow. No wasted time, no friction.",
                        "expected_emotions": ["flow"]
                    },
                    {
                        "text": "Sophia: I appreciate how each of us is proactive. It’s pure mutual respect.",
                        "expected_emotions": ["mutual respect"]
                    },
                    {
                        "text": "Tom: I’m proud of how we handle new challenges instantly. Feels like big confidence.",
                        "expected_emotions": ["self-confidence", "pride in work"]
                    },
                    {
                        "text": "Liam: We soared past initial targets. I'm excited to finalize advanced features.",
                        "expected_emotions": ["enthusiasm about goals"]
                    },
                    {
                        "text": "Sophia: Yes, the sense of accomplishment is massive. Let’s keep pushing forward.",
                        "expected_emotions": ["accomplishment"]
                    },
                    {
                        "text": "Tom: A quick retrospective might help us optimize even more.",
                        "expected_emotions": ["confidence in team"]
                    },
                    {
                        "text": "Sophia: Agreed. The synergy is real, and the outcomes are top-notch.",
                        "expected_emotions": ["synergy", "satisfaction with outcomes"]
                    },
                    {
                        "text": "Liam: The way we collaborate seamlessly is truly impressive.",
                        "expected_emotions": ["synergy"]
                    },
                    {
                        "text": "Sophia: Our mutual respect allows us to tackle any obstacle with ease.",
                        "expected_emotions": ["mutual respect"]
                    },
                    {
                        "text": "Tom: I feel empowered by our trust in each other’s abilities.",
                        "expected_emotions": ["empowerment", "trust"]
                    },
                    {
                        "text": "Liam: It's exhilarating to see our productivity levels soar like this.",
                        "expected_emotions": ["enthusiasm about goals"]
                    },
                    {
                        "text": "Sophia: I’m confident that we can achieve even more in the next sprint.",
                        "expected_emotions": ["confidence in team"]
                    },
                    {
                        "text": "Tom: The flow we’ve established makes every day feel efficient and productive.",
                        "expected_emotions": ["flow"]
                    },
                    {
                        "text": "Liam: Our commitment to excellence is what sets us apart.",
                        "expected_emotions": ["commitment"]
                    },
                    {
                        "text": "Sophia: I love the camaraderie we share. It makes work enjoyable.",
                        "expected_emotions": ["camaraderie"]
                    },
                    {
                        "text": "Tom: Reflecting on our progress, I’m proud of our continuous improvement.",
                        "expected_emotions": ["pride in work", "sense of growth"]
                    },
                    {
                        "text": "Sophia: Let’s maintain this momentum and aim for even higher achievements.",
                        "expected_emotions": ["enthusiasm about goals", "accomplishment"]
                    }
                ]
            },
            {
                "team_name": "TeamAdjourning",
                "expected_stage": "Adjourning",
                "lines": [
                    {
                        "text": "Emma: We’re basically finished. I have a bittersweet feeling we'll disband soon.",
                        "expected_emotions": ["sense of loss"]
                    },
                    {
                        "text": "Oliver: I'm glad we succeeded, but there's a real sadness about closure.",
                        "expected_emotions": ["sadness about closure"]
                    },
                    {
                        "text": "Sophia: Looking back at the start makes me nostalgic for the group.",
                        "expected_emotions": ["nostalgia for the group"]
                    },
                    {
                        "text": "Emma: Odd not having daily calls soon, but I'm excited for what's next too.",
                        "expected_emotions": ["enthusiasm for the future", "uncertainty about next steps"]
                    },
                    {
                        "text": "Oliver: I guess it's normal. Let's do a final retrospective tomorrow.",
                        "expected_emotions": ["reflection on achievements"]
                    },
                    {
                        "text": "Sophia: Part of me is relieved it's over, but I'll miss it. Feels like closure.",
                        "expected_emotions": ["relief from completion", "closure"]
                    },
                    {
                        "text": "Emma: There's some emptiness, but also grateful for all we learned.",
                        "expected_emotions": ["emptiness after disbandment", "thankfulness for the experience"]
                    },
                    {
                        "text": "Oliver: We overcame so much. I'm proud, but I sense a loss not continuing together.",
                        "expected_emotions": ["sense of loss"]
                    },
                    {
                        "text": "Sophia: I hope we keep in touch. Maybe a new project will reunite us someday.",
                        "expected_emotions": ["enthusiasm for the future"]
                    },
                    {
                        "text": "Emma: Yes. I'll remember this journey fondly. Let’s officially wrap up.",
                        "expected_emotions": ["closure", "nostalgia for the group"]
                    },
                    {
                        "text": "Oliver: It's hard to say goodbye, but I'm thankful for the time we've spent.",
                        "expected_emotions": ["thankfulness for the experience", "sense of loss"]
                    },
                    {
                        "text": "Sophia: Looking forward to new beginnings, but I’ll miss our teamwork.",
                        "expected_emotions": ["enthusiasm for the future", "sense of loss"]
                    },
                    {
                        "text": "Emma: I feel a mix of sadness and excitement about what's ahead.",
                        "expected_emotions": ["sense of loss", "enthusiasm for the future"]
                    },
                    {
                        "text": "Oliver: Our accomplishments will always remind me of how we worked together.",
                        "expected_emotions": ["pride in work"]
                    },
                    {
                        "text": "Sophia: Even though we're disbanding, the memories will last.",
                        "expected_emotions": ["nostalgia for the group"]
                    },
                    {
                        "text": "Emma: Let's ensure we celebrate our successes before we part ways.",
                        "expected_emotions": ["satisfaction with outcomes"]
                    },
                    {
                        "text": "Oliver: I’m uncertain about the next steps, but I trust we'll find new paths.",
                        "expected_emotions": ["uncertainty about next steps", "trust"]
                    },
                    {
                        "text": "Sophia: I’m grateful for the support we provided each other through thick and thin.",
                        "expected_emotions": ["thankfulness for the experience", "empathy"]
                    },
                    {
                        "text": "Emma: The journey has been incredible. I feel relieved knowing it's concluded well.",
                        "expected_emotions": ["relief from completion"]
                    },
                    {
                        "text": "Oliver: We should document our lessons learned for future projects.",
                        "expected_emotions": ["reflection on achievements"]
                    }
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
        self.create_excel_summary(self.results, "scenarios_results.xlsx")

    def create_excel_summary(self, results, filename):
        df = pd.DataFrame(results)
        df.to_excel(filename, index=False)
        print(f"Excel results saved to {filename}")

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == "__main__":
    unittest.main()
