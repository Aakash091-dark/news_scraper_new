import subprocess
import json
import time
import glob
import shutil
import logging
from HELPER.news_classifier import classify_news
from HELPER.key_extractor import extract_keywords

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def run_rss_ingestion():
    logging.info("Starting RSS ingestion...")
    try:
        pass 
    except subprocess.CalledProcessError as e:
        logging.error(f"RSS ingestion failed: {e}")
        raise

def run_gn():
    logging.info("Running GN.py (Google Discovery keyword metadata search)...")
    try:
        subprocess.run(["python", "GN.py"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"GN.py failed: {e}")
        raise

def classify_metadata_categories():
    logging.info("Classifying news metadata from GN.py output...")
    try:
        with open("search_results.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data.get("results", []):
            title = item.get("title", "")
            description = item.get("description", "")
            category, subcategory = classify_news(title, description)
            item["category"] = category
            item["subcategory"] = subcategory

        with open("search_results_with_categories.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info("Metadata classification complete.")
    except Exception as e:
        logging.error(f"Failed to classify metadata: {e}")
        raise

def run_gnw():
    logging.info("Running GNW.py (Scraper for full news content)...")
    try:
        subprocess.run(["python", "GNW.py"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"GNW.py failed: {e}")
        raise

def extract_keywords_post_gnw():
    logging.info("Extracting keywords from full news scraped by GNW.py...")
    data_files = glob.glob("data/*.json")

    for filepath in data_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                articles = json.load(f)
        except Exception as e:
            logging.warning(f"Skipping unreadable file {filepath}: {e}")
            continue

        updated = False
        for article in articles:
            full_news = article.get("content") or article.get("full_news") or ""
            if not full_news:
                continue

            try:
                keywords = extract_keywords(full_news)
                if keywords:
                    article["keywords"] = keywords
                    updated = True
            except Exception as e:
                logging.warning(f"Keyword extraction failed for one article in {filepath}: {e}")

        if updated:
            try:
                shutil.copy(filepath, filepath + ".bak")  # optional backup
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(articles, f, indent=2, ensure_ascii=False)
                logging.info(f"Updated keywords in: {filepath}")
            except Exception as e:
                logging.error(f"Failed to update {filepath}: {e}")

def main():
    try:
        run_rss_ingestion()
        time.sleep(2)
        run_gn()
        classify_metadata_categories()
        run_gnw()
        extract_keywords_post_gnw()
        logging.info("✅ Pipeline complete!")
    except Exception as e:
        logging.critical(f"Pipeline aborted due to error: {e}")

if __name__ == "__main__":
    main()
