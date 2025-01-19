A chatbot developed as part of a Bachelor research project at the University of Twente, designed to understand team emotions and map them to Tuckman’s stages of team development: Forming, Storming, Norming, Performing, and Adjourning.

## Features

**Emotion Detection**: Utilizes a zero-shot classification model to identify emotional cues in user text. 
**Stage Mapping**: Associates detected emotions with corresponding stages in Tuckman’s team development model.
**Feedback Generation**: Provides stage-specific recommendations to enhance team dynamics and performance.
**Conversation & Analysis Modes**: Allows for real-time conversation tracking or bulk analysis of team communications.
**Feedback Popup**: Offers detailed feedback through a user-friendly interface.
**File Upload Support**: Enables analysis of chat logs through text file uploads.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── chatbot_generative.py
│   ├── db.py
│   ├── emotion_analysis.py
│   ├── main.py
│   ├── stage_mapping.py
│   └── database.db
├── chatbot_llama/
├── tests/
│   ├── test_scenarios.py
│   ├── test_scenarios_old.py
│   ├── test_classify_msg_relevance.py
├── index.html
├── avatar.png 
├── styles.css
├── app.js
├── requirements.txt
└── README.md

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
