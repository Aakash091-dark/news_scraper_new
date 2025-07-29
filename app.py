import time
import os
from CORE import rss_functions
from CORE import rss_websites
from WEB_SCRAPPING import google_search_for_query
from proxy import proxy_content
from DB_RECTIFIER import check_and_add_json
from DATABASE.create import build_DB
import asyncio


def delay():
    time.sleep(10 * 60)


def get_source(full_source):
    parts = full_source.split("_")
    full_name = full_source
    source = parts[0]
    source_category = parts[1]
    return full_name, source, source_category


def app():
    build_DB()
    for key, value in rss_websites.items():
        full_name, source, source_category = get_source(key)
        json_file = os.path.join("data", f"{full_name}.json")
        csv_file = os.path.join("log/", f"{full_name}.csv")
        # try:
        rss_url = proxy_content(value)
        if full_name in rss_functions:
            rss = rss_functions[full_name](
                rss_url, json_file, csv_file, source, source_category
            )
        else:
            rss = rss_functions["all_rss"](
                rss_url, json_file, csv_file, source, source_category
            )
        # google = asyncio.run(google_search_for_query())
        print("*" * 40)
        # print(google)
        print(rss)
        print("*" * 40)
        print("#" * 40)
        check = check_and_add_json(json_file)

        print("#" * 40)

    print(
        "DELAY!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    )
    delay()


if __name__ == "__main__":
    app()
