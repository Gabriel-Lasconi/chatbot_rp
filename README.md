A chatbot developed as part of a Bachelor research project at the University of Twente, designed to understand team emotions and map them to Tuckman’s stages of team development: Forming, Storming, Norming, Performing, and Adjourning.

## Features

- **Emotion Detection:** Uses a zero-shot classification model to find emotional cues in user text.
- **Stage Mapping:** Connects the detected emotion to a relevant Tuckman stage.
- **Feedback Generation:** Provides stage-based recommendations to help improve team dynamics.

## Project Structure

```
app/
    __init__.py
    chatbot_generative.py
    db.py
    emotion_analysis.py
    main.py
    stage_mapping.py
    teams.db
chatbot_llama/
tests/
    test_emotion_analysis.py
    test_emotion_analysis_scenario.py
    test_scenarios_analysis_mode.py
    test_stage_mapper.py
index.html
styles.css
app.js
requirements.txt
README.md
```

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
   Open the browser at `http://127.0.0.1:8000` and interact with the chatbot.
