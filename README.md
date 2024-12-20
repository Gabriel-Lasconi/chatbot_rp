This project is a chatbot developed during my Bachelor research project at the University of Twente and designed to understand team emotions and map them to Tuckman’s stages of team development (Forming, Storming, Norming, Performing, and Adjourning).

## Features

- **Emotion Detection:** Uses a zero-shot classification model to find emotional cues in user text.
- **Stage Mapping:** Connects the detected emotion to a relevant Tuckman stage.
- **Feedback Generation:** Provides stage-based recommendations to help improve team dynamics.

## Project Structure

```
app/
    __init__.py
    chatbot.py
    emotion_analysis.py
    main.py
    preprocess.py
    stage_mapping.py
    chat_logs.json
tests/
    test_chatbot.py
    test_emotion_analysis.py
ui/
    index.html
    styles.css
    app.js
requirements.txt
README.md
```

- **chatbot.py:** Basic chatbot logic that asks questions and handles user responses.
- **emotion_analysis.py:** Identifies emotions from text.
- **main.py:** Runs the application, provides endpoints.
- **preprocess.py:** Cleans and prepares text before analysis.
- **stage_mapping.py:** Maps emotions to Tuckman’s stages and gives feedback based on that.
- **chat_logs.json:** Stores conversation logs if enabled.
- **tests/:** Contains Python test files for verifying chatbot and emotion analysis logic.
- **ui/:** Contains a simple front-end interface to interact with the chatbot.

## How to Use

1. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```
   
2. **Run the App:**
   ```bash
   uvicorn app.main:app --reload
   ```
   
3. **Interact with the Chatbot:**
   Open your browser at `http://127.0.0.1:8000` and use the provided endpoints to send messages and reset conversations.
