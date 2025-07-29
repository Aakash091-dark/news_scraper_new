import re
from typing import Tuple, Dict, List

# ----- Global configuration -----

CATEGORY_RULES = {
    "Politics": ["election", "government", "parliament", "senate", "congress", "law", "political",
                 "minister", "president", "prime minister", "voting", "democracy", "republican",
                 "democrat", "policy", "legislation", "bill", "constitution", "diplomat", "embassy"],
    "Business": ["stock", "market", "economy", "finance", "business", "trade", "investment",
                 "company", "corporation", "profit", "revenue", "earnings", "merger", "acquisition",
                 "startup", "entrepreneur", "banking", "cryptocurrency", "bitcoin", "nasdaq", "dow"],
    "Technology": ["technology", "software", "AI", "machine learning", "gadgets", "internet",
                   "computer", "smartphone", "app", "digital", "cyber", "tech", "innovation",
                   "programming", "coding", "algorithm", "data", "cloud", "5G", "IoT", "blockchain"],
    "Sports": ["football", "cricket", "tennis", "basketball", "soccer", "olympics", "sports",
               "match", "game", "tournament", "championship", "player", "team", "coach",
               "goal", "score", "victory", "defeat", "league", "fifa", "ipl", "nba"],
    "Health": ["health", "medicine", "virus", "covid", "doctor", "medical", "vaccine",
               "hospital", "patient", "disease", "treatment", "therapy", "drug", "pharmaceutical",
               "pandemic", "epidemic", "surgery", "diagnosis", "wellness", "mental health"],
    "Entertainment": ["movie", "music", "celebrity", "film", "show", "entertainment", "tv",
                      "actor", "actress", "singer", "concert", "album", "netflix", "bollywood",
                      "hollywood", "theater", "drama", "comedy", "series", "streaming"],
    "Education": ["education", "school", "university", "college", "student", "teacher", "exam",
                  "study", "research", "academic", "learning", "scholarship", "degree", "graduation"],
    "Environment": ["environment", "climate", "weather", "pollution", "global warming", "renewable",
                    "energy", "solar", "wind", "carbon", "emission", "conservation", "wildlife"],
    "International": ["international", "global", "world", "foreign", "country", "nation", "border",
                      "diplomatic", "treaty", "war", "conflict", "peace", "united nations", "eu"]
}

DEFAULT_CATEGORY = "General"
DEFAULT_SUBCATEGORY = "Miscellaneous"

# ----- Utility functions -----

def preprocess(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s\'-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def compile_patterns() -> Dict[str, re.Pattern]:
    compiled = {}
    for cat, keywords in CATEGORY_RULES.items():
        pattern = '|'.join([rf'\b{re.escape(k.lower())}\b' for k in keywords])
        compiled[cat] = re.compile(pattern, re.IGNORECASE)
    return compiled

compiled_category_patterns = compile_patterns()

def score_category(text: str, category: str) -> int:
    return len(compiled_category_patterns[category].findall(text))

def fallback_category(text: str) -> str:
    if any(word in text for word in ['news', 'report', 'update', 'announce']):
        return "General"
    if re.search(r'\d+%|\$\d+|\d+\s*(million|billion|thousand)', text):
        return "Business"
    if re.search(r'\b(usa|india|china|uk|europe|asia|africa)\b', text):
        return "International"
    return DEFAULT_CATEGORY

# ----- Main classifier -----

def classify_news(title: str, description: str = "") -> Tuple[str, str]:
    text = preprocess(f"{title or ''} {description or ''}")
    if not text:
        return DEFAULT_CATEGORY, DEFAULT_SUBCATEGORY

    scores = {cat: score_category(text, cat) for cat in CATEGORY_RULES}
    scores = {k: v for k, v in scores.items() if v > 0}

    if scores:
        best_category = max(scores.items(), key=lambda x: x[1])[0]
    else:
        best_category = fallback_category(text)

    best_subcategory = DEFAULT_SUBCATEGORY  # You can plug in your subcategory logic here if needed
    return best_category, best_subcategory

def get_category_confidence(title: str, description: str = "") -> Dict[str, float]:
    text = preprocess(f"{title or ''} {description or ''}")
    if not text:
        return {DEFAULT_CATEGORY: 1.0}
    
    scores = {cat: score_category(text, cat) for cat in CATEGORY_RULES}
    total = sum(scores.values())
    if total == 0:
        return {DEFAULT_CATEGORY: 1.0}
    
    return {cat: score / total for cat, score in scores.items() if score > 0}

def get_all_categories() -> List[str]:
    return list(CATEGORY_RULES.keys()) + [DEFAULT_CATEGORY]

'''
# Example usage and testing
def classify_news(title: str, description: str = "") -> Tuple[str, str]:
    """
    Convenience function for backward compatibility
    """
    classifier = NewsClassifier()
    return classifier.classify_news(title, description)


if __name__ == "__main__":
    # Test the classifier
    classifier = NewsClassifier()
    
    test_cases = [
        ("Election Results 2024", "The latest election results are in with surprising outcomes"),
        ("Stock Market Crashes", "Major indices fall by 5% amid economic concerns"),
        ("New AI Technology", "Revolutionary machine learning algorithm developed by tech giants"),
        ("Murder Investigation", "Police investigate suspicious death in downtown area"),
        ("COVID-19 Vaccine Update", "New vaccine shows promising results in clinical trials"),
        ("", ""),  # Empty case
        ("Breaking News", "Important announcement today"),  # Vague case
    ]
    
    print("News Classification Results:")
    print("-" * 50)
    
    for title, desc in test_cases:
        category, subcategory = classifier.classify_news(title, desc)
        confidence = classifier.get_category_confidence(title, desc)
        is_crime = classifier.is_crime_related(title, desc)
        
        print(f"Title: {title or 'Empty'}")
        print(f"Description: {desc or 'Empty'}")
        print(f"Category: {category}")
        print(f"Subcategory: {subcategory}")
        print(f"Crime-related: {is_crime}")
        print(f"Top confidence scores: {dict(list(sorted(confidence.items(), key=lambda x: x[1], reverse=True))[:3])}")
        print("-" * 30)'''