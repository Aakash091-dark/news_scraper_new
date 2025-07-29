import re
from datetime import datetime
import os
import sys
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# insert it so that python can resolve the package
sys.path.insert(0, base_dir)
from WEB_SCRAPPING.google_cse import google_cse_search

async def google_search_for_query(
    query="warehouses in india",
) -> dict:

    context = []
    sources = []
    results_list = []


    if isinstance(query, list):
        for q in query:
            try:
                results = await google_cse_search(q)
                if results:
                        results_list.append(results)
            except Exception as e:
                print(f"[fetch_google] CSE search threw: {e}")
                return context
                continue
    else:
            try:
                results = await google_cse_search(query)
                if results:
                    results_list.append(results)
            except Exception as e:
                print(f"[fetch_google] CSE search threw for query {query}: {e}")
                
    
    
              
    if not results_list:
        return context
    
    if isinstance(results_list,list):
         return results_list
    else:
         return results_list[0]

