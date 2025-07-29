# key_extractor.py

from rake_nltk import Rake
import nltk

# Download necessary NLTK resources (once)
nltk.download('stopwords')
nltk.download('punkt')

def extract_keywords(text: str, max_keywords=10) -> list:
    """
    Extract top keywords from text using RAKE algorithm.
    Returns a list of keywords/phrases.
    """
    if not text:
        return []

    r = Rake()  # Uses NLTK stopwords by default
    r.extract_keywords_from_text(text)
    ranked_phrases = r.get_ranked_phrases()

    # Return top max_keywords phrases
    return ranked_phrases[:max_keywords]

'''
if __name__ == "__main__":
    sample_text = ("The stock market crashed today, with major indices losing points "
                   "due to economic uncertainty and inflation concerns.")
    keywords = extract_keywords(sample_text)
    print("Extracted keywords:", keywords)'''
