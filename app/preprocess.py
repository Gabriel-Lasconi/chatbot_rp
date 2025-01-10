# #app/preprocess.py - linguistic processing and cleaning the user inputs
#
# import re
# import spacy
#
# class Preprocessor:
#     def __init__(self):
#         self.nlp = spacy.load("en_core_web_sm")
#
#     def clean(self, text: str, preprocess: bool = False) -> str:
#         """
#         Preprocess the text or return it as is based on the flag.
#
#         Args:
#             text (str): The user input.
#             preprocess (bool): Whether to preprocess the text or not.
#
#         Returns:
#             str: The cleaned or raw text.
#         """
#         if not preprocess:
#             return text  # Skip preprocessing and return the raw text
#
#         if not text.strip():
#             return ""
#
#         # Preprocessing logic
#         text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
#         text = re.sub(r"\s+", " ", text).strip()
#
#         doc = self.nlp(text.lower())
#         cleaned_text = " ".join([token.lemma_ for token in doc if not token.is_stop])
#
#         return cleaned_text
