import requests
import os
import json
from requests.exceptions import Timeout, RequestException
from dotenv import load_dotenv
from urllib.parse import urlencode
from HELPER.cse_date_formatter import extract_date_and_description

load_dotenv()
CSE_API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")




def google_cse_search(query: str) -> list:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": CSE_API_KEY,
        "cx": CSE_SEARCH_ENGINE_ID,
        "q": query,
        "num": 10
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Timeout:
        # If the request times out, return an empty list
        print(f"Google CSE request timed out for query: {query!r}")
        return []
    except RequestException as e:
        # Catch other network‐level errors (DNS failure, 4xx/5xx, etc.)
        print(f"Google CSE request failed: {e}")
        return []

    if "items" not in data:
        err_msg = data.get("error", {}).get("message", "Unknown")
        print(f"No results. Error: {err_msg}")
        return []

    search_results = []
    for item in data["items"]:
        Title = item["title"]
        Link = item["link"]
        results = extract_date_and_description(item.get("snippet", ""))
        Date = results["date"]
        Description = results["description"]
        search_results.append({
            "title":Title,
            "link": Link,
            "date": Date,
            "description": Description
        })
        
    

    
    search_results_structured = json.dumps(search_results, indent=4)
    return search_results_structured

