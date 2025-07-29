import subprocess
import json
import time
import glob
import logging
import sys
import os

from HELPER.key_extractor import extract_keywords
from DB_RECTIFIER.news_matcher_and_added import NEWS_SCORE, add_news_in_db
from WEB_SCRAPPING.GNW import infer_source_name
from rss_functions.ALL_RSS import all_rss
from CORE.websites import rss_websites, rss_functions
from proxy.oxylab import proxy_content
from HELPER.news_classifier import classify_news  # Correct import
 # Instance of classifier

def get_source(full_source):
    parts = full_source.split("_")
    source = parts[0]
    source_category = parts[1] if len(parts) > 1 else "general"
    return full_source, source, source_category

# Optional fallback RSS function if source not found
def fallback_rss_handler(rss_url, json_file, csv_file, source, category):
    logging.warning(f"Using fallback RSS handler for source: {source}")
    return all_rss(rss_url, json_file, csv_file, source, category)

def run_rss_ingestion():
    logging.info("Starting RSS ingestion...")
    for key, value in rss_websites.items():
        full_name, source, source_category = get_source(key)
        json_file = os.path.join("data", f"{full_name}.json")
        csv_file = os.path.join("log", f"{full_name}.csv")

        rss_url = proxy_content(value)

        rss_func = rss_functions.get(full_name, fallback_rss_handler)
        try:
            rss_func(rss_url, json_file, csv_file, source, source_category)
        except Exception as e:
            logging.error(f"Error processing {key}: {e}")

def run_gn():
    print("Running GN.py (Google Discovery metadata search)...")
    subprocess.run([sys.executable, "WEB_SCRAPPING/GNW.py"], check=True)

def classify_metadata_categories():
    print("Classifying GN.py metadata results with news_classifier...")
    with open("search_results.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data.get("results", []):
        title = item.get("title", "")
        description = item.get("description", "")
        category, subcategory = classify_news(title, description)  # FIXED CALL
        item["category"] = category
        item["subcategory"] = subcategory

    with open("search_results_with_categories.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Classification completed and saved to search_results_with_categories.json")

def run_gnw():
    print("Running GNW.py (Full article scraper)...")
    subprocess.run([sys.executable, "WEB_SCRAPPING/GN.py"], check=True)

def extract_keywords_post_gnw():
    print("Extracting keywords from full news content post-GNW.py scraping...")
    data_files = glob.glob("data/*.json")

    for filepath in data_files:
        with open(filepath, "r", encoding="utf-8") as f:
            articles = json.load(f)

        updated = False
        for article in articles:
            full_news = article.get("content") or article.get("full_news") or article.get("full_content", "")
            if not full_news:
                continue
            keywords = extract_keywords(full_news)
            if keywords:
                article["keywords"] = keywords
                updated = True

        if updated:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)

    print("Keyword extraction completed and saved.")

def insert_articles_to_db():
    print("Inserting articles into database with deduplication...")
    data_files = glob.glob("data/*.json")
    total_inserted = 0

    for filepath in data_files:
        with open(filepath, "r", encoding="utf-8") as f:
            articles = json.load(f)

        for article in articles:
            full_news = article.get("content") or article.get("full_news") or article.get("full_content", "")
            if not full_news:
                continue

            title = article.get("title", "")
            description = article.get("description", "")
            source = article.get("source")

            if not source:
                url = article.get("url") or article.get("link")
                source = infer_source_name(url) if url else "Unknown"

            category = article.get("category")
            subcategory = article.get("subcategory")
            article_category = []

            if category:
                article_category.append({"category": category, "subcategory": subcategory})

            similar_id, somewhat_similar_id, vector_embeddings = NEWS_SCORE(article)

            add_news_in_db(
                article,
                vector_embeddings,
                full_news,
                article_category,
                similar_id,
                somewhat_similar_id,
            )
            total_inserted += 1

    print(f"Inserted {total_inserted} articles into the database.")

def app():
    run_rss_ingestion()
    time.sleep(2)

    run_gn()
    time.sleep(2)

    classify_metadata_categories()
    time.sleep(2)

    run_gnw()
    time.sleep(2)

    extract_keywords_post_gnw()
    time.sleep(2)

    insert_articles_to_db()
    print("Pipeline complete.")

if __name__ == "__main__":
    app()
