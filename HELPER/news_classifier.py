# news_classifier.py

import re

# Define some example categories and keywords
CATEGORY_RULES = {
    "Politics": ["election", "government", "parliament", "senate", "law", "political"],
    "Business": ["stock", "market", "economy", "finance", "business", "trade", "investment"],
    "Technology": ["technology", "software", "AI", "machine learning", "gadgets", "internet"],
    "Sports": ["football", "cricket", "tennis", "basketball", "soccer", "olympics", "sports"],
    "Health": ["health", "medicine", "virus", "covid", "doctor", "medical", "vaccine"],
    "Entertainment": ["movie", "music", "celebrity", "film", "show", "entertainment", "tv"],
}

SUBCATEGORY_RULES = {
    "Politics": {
        "Elections": ["election", "vote", "campaign"],
        "Government": ["parliament", "policy", "law"],
    },
    "Business": {
        "Stock Market": ["stock", "share", "index"],
        "Economy": ["economy", "gdp", "inflation"],
    },
    "Technology": {
        "AI": ["artificial intelligence", "AI", "machine learning"],
        "Gadgets": ["smartphone", "laptop", "gadgets"],
    },
    # Add more as needed
}


def classify_news(title: str, description: str):
    """
    Classify news category and subcategory based on title and description.
    Returns (category, subcategory) or (None, None) if undetermined.
    """
    text = (title or "") + " " + (description or "")
    text = text.lower()

    category = None
    subcategory = None

    # Find category
    for cat, keywords in CATEGORY_RULES.items():
        if any(re.search(r'\b' + re.escape(k) + r'\b', text) for k in keywords):
            category = cat
            # Check subcategory for this category
            if cat in SUBCATEGORY_RULES:
                for subcat, sub_keywords in SUBCATEGORY_RULES[cat].items():
                    if any(re.search(r'\b' + re.escape(k) + r'\b', text) for k in sub_keywords):
                        subcategory = subcat
                        break
            break

    return category, subcategory

'''
if __name__ == "__main__":
    test_title = "Government announces new election dates"
    test_description = "The parliament declared that the upcoming elections will be held next month."
    cat, subcat = classify_news(test_title, test_description)
    print(f"Category: {cat}, Subcategory: {subcat}")'''
