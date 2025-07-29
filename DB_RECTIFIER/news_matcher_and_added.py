from .llm_response import llm_true_false
from HELPER.embeddings import NOMIC_EMBEDDINGS
from DATABASE.fetch import if_unique_data, HideFilteredResults
from DATABASE.insert import (
    insertPrimaryTable,
    insertSecondTable,
    insertVECTORSTable,
    insertUniqueNewsInDB,
    insertDuplicateNewsInDB,
)
from HELPER.check_similarity import check_cosine_similarity
import uuid
import os


nomic = NOMIC_EMBEDDINGS()
import json


def NEWS_SCORE(news):
    news_url = news["link"]
    news_short = str(news["title"] + ", details :" + news["description"])
    vector_embeddings = nomic.embed_text(news_short)
    Filter_results = HideFilteredResults("VECTORS_TABLE", "METADATA", news_url)
    similar_news_id, somewhat_similar_news_id = check_cosine_similarity(
        vector_embeddings, Filter_results
    )
    return similar_news_id, somewhat_similar_news_id, vector_embeddings


def add_news_in_db(
    current_news,
    current_news_embeddings,
    FULL_NEWS,
    source_category,
    similar_news_id,
    somewhat_similar_news_id,
):

    # unique news
    if similar_news_id == None and somewhat_similar_news_id == None:
        insertUniqueNewsInDB(
            current_news, current_news_embeddings, source_category, FULL_NEWS
        )

    # dublicate news
    if somewhat_similar_news_id:
        insertDuplicateNewsInDB(
            somewhat_similar_news_id,
            current_news,
            source_category,
            current_news_embeddings,
            FULL_NEWS,
        )


def check_and_add_json(json_file):
    count = 0
    l = []
    with open(json_file, "r", encoding="utf-8") as f:
        news_json = json.load(f)
    os.remove(json_file)
    return len(news_json)  # Return the count of news items processed
