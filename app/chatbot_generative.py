# app/chatbot_generative.py - class where I am trying to implement a different type of chatbot that generates messages automatically
# for now this class is not in use


from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from app.emotion_analysis import EmotionDetector
from app.stage_mapping import StageMapper
import torch


class ChatbotGenerative:
    def __init__(self):
        self.model_name = "tiiuae/falcon-40b"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            trust_remote_code=True
        )

        self.emotion_detector = EmotionDetector()
        self.stage_mapper = StageMapper()

        self.chat_history = []
        self.questions_asked = 0
        self.max_questions = 3

        # instructions
        self.system_instructions = (
            "You are a helpful assistant that identifies a team's emotional climate "
            "and maps it to Tuckman's stages. Over the course of up to 3 user responses, "
            "ask natural follow-up questions about the team's feelings, then provide concluding feedback."
        )

    def _build_prompt(self, user_message):
        """
        Build the prompt according to Falcon chat format.
        """
        conversation_str = "\n".join(self.chat_history)

        prompt = (
            f"System: {self.system_instructions}\n\n"
            f"{conversation_str}\n"
            f"User: {user_message}\n"
            "Assistant:"
        )
        return prompt

    def _generate_response(self, user_message):
        """
        Generate a response using the Falcon model.
        """
        prompt = self._build_prompt(user_message)

        gen_config = GenerationConfig(
            max_new_tokens=200,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            do_sample=True
        )

        inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        with torch.no_grad():
            output = self.model.generate(**inputs, generation_config=gen_config)

        response = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()

        if "Assistant:" in response:
            assistant_response = response.split("Assistant:", 1)[-1].strip()
        else:
            assistant_response = response

        self.chat_history.append(f"User: {user_message}")
        self.chat_history.append(f"Assistant: {assistant_response}")

        return assistant_response

    def process_message(self, text):
        """
        Process the user's message, detect emotions, map to a stage, and generate a response.
        """
        try:
            emotion_results = self.emotion_detector.detect_emotion(text)
            dominant_emotion = emotion_results["label"]

            stage = self.stage_mapper.map_emotion_to_stage(dominant_emotion)
            feedback = self.stage_mapper.get_feedback_for_stage(stage)

            self.questions_asked += 1

            if self.questions_asked < self.max_questions:
                bot_response = self._generate_response(text)
                return {"bot_message": bot_response, "stage": None, "feedback": None}
            else:
                bot_response = self._generate_response(text)
                return {"bot_message": bot_response, "stage": stage, "feedback": feedback}

        except Exception as e:
            print(f"[ERROR] {e}")
            return {"bot_message": "An error occurred. Please try again.", "stage": "Error", "feedback": None}

    def reset_conversation(self):
        """
        Reset the conversation state.
        """
        self.questions_asked = 0
        self.chat_history = []


if __name__ == "__main__":
    chatbot = ChatbotGenerative()
    print("Chatbot is ready! Type 'reset' to reset the conversation or 'exit' to quit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        elif user_input.lower() == "reset":
            chatbot.reset_conversation()
            print("Conversation reset.")
        else:
            result = chatbot.process_message(user_input)
            print("Bot:", result["bot_message"])
            if result["feedback"]:
                print("Bot (Stage Feedback):", result["feedback"])
