#app/preprocess.py - linguistic processing and cleaning the user inputs

import re
import spacy


class Preprocessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def clean(self, text: str) -> str:
        """
        Clean the input text by removing special characters, extra spaces, and converting to lowercase.

        Args:
            text (str): The user input.

        Returns:
            str: The cleaned text.
        """
        if not text.strip():
            return ""

        #Get rid of special characters or extra unnecesarry spaces
        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        doc = self.nlp(text.lower())
        cleaned_text = " ".join([token.lemma_ for token in doc if not token.is_stop])

        return cleaned_text
