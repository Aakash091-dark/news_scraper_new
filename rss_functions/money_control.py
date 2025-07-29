import feedparser
import json
import csv
import os
from datetime import datetime

def ensure_directories():
    os.makedirs("log", exist_ok=True)
    os.makedirs("data", exist_ok=True)

def log_statistics(new_count: int, duplicate_count: int, csv_file: str = "log/rss_statistics_moneycontrol.csv"):
    ensure_directories()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(csv_file)
    
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "New Titles", "Duplicate Titles", "Total Processed"])
        writer.writerow([timestamp, new_count, duplicate_count, new_count + duplicate_count])

def moneycontrol_rss(rss_url: str, output_file: str = "data/moneycontrol.json"):
    ensure_directories()
    
    # Load existing data
    existing_titles = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_titles = {item["title"] for item in existing_data}
        except (json.JSONDecodeError, FileNotFoundError):
            existing_data = []
    else:
        existing_data = []
    
    # Parse RSS feed
    feed = feedparser.parse(rss_url)
    print("feed------------------------------------->", feed)
    new_items = []
    new_count = 0
    duplicate_count = 0
    
    for entry in feed.entries:
        title = entry.get("title", "")
        
        if title in existing_titles:
            duplicate_count += 1
        else:
            new_count += 1
            item = {
                "title": title,
                "link": entry.get("link", ""),
                "description": entry.get("description", ""),
                "pubDate": entry.get("published", "")
            }
            new_items.append(item)
            existing_titles.add(title)  
    
    all_items = existing_data + new_items
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_items, f, indent=4, ensure_ascii=False)
    
    log_statistics(new_count, duplicate_count)
    
    print(f"moneycontrol rss Processing complete: {new_count} new titles, {duplicate_count} duplicates")
    print(f"Data saved to: {output_file}")
    print(f"Log saved to: log/rss_statistics_moneycontrol.csv")
    
    return json.dumps(all_items, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    url = "https://www.moneycontrol.com/rss/latestnews.xml"
    json_data = moneycontrol_rss(url)
    print(json_data)