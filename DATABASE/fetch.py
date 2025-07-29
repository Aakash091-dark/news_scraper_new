import psycopg2
import os
from dotenv import load_dotenv
from .getDatabase import wait_for_connection
from urllib.parse import urlparse
import re 

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

allowed_columns = {
    "PRIMARY_TABLE": [
        "PRIMARY_ARTICLE_ID", "ARTICLE_ID", "TITLE", "URL",
        "DESCRIPTION", "NEWS_SOURCE", "PUBLISH_DATE",
    ],
    "SECOND_TABLE": [
        "PRIMARY_ARTICLE_ID UUID",
                        "ARTICLE_ID UUID PRIMARY KEY",
                        "TITLE TEXT NOT NULL",
                        "URL TEXT UNIQUE",
                        "DESCRIPTION TEXT",
                        "PUBLISH_DATE TEXT",
                        "ARTICLE_SOURCE TEXT",
                        "SCRAPED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                        "SCRAP_VERSION TEXT",
    ],
    "VECTORS_TABLE": ["ARTICLE_ID", "EMBEDDINGS", "METADATA"],
    "CATEGORY_TABLE": ["ARTICLE_ID", "SOURCE_ARTICLE_ID", "SOURCE"],
    "KEYWORDS_TABLE": ["ARTICLE_ID", "KEYWORD"],
}


def if_unique_data(table: str, column: str, value):
    if table not in allowed_columns:
        raise ValueError(f"Table '{table}' is not allowed.")

    if column not in allowed_columns[table]:
        raise ValueError(f"Column '{column}' not allowed in table '{table}'.")

    query = f"SELECT 1 FROM {table} WHERE {column} = %s LIMIT 1;"

    conn = wait_for_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (value,))
            return cursor.fetchone() is None
    finally:
        conn.close()


def HideFilteredResults(table: str, column: str, value):
    if table not in allowed_columns:
        raise ValueError(f"Table '{table}' is not allowed.")

    if column not in allowed_columns[table]:
        raise ValueError(f"Column '{column}' not allowed in table '{table}'.")

    query = f"SELECT * FROM {table} WHERE {column} != %s"

    conn = wait_for_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (value,))
            return cursor.fetchall()
    finally:
        conn.close()


def ShowFilteredResults(table: str, column: str, value):
    if table not in allowed_columns:
        raise ValueError(f"Table '{table}' is not allowed.")

    if column not in allowed_columns[table]:
        raise ValueError(f"Column '{column}' not allowed in table '{table}'.")

    query = f"SELECT * FROM {table} WHERE {column} = %s"

    conn = wait_for_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (value,))
            return cursor.fetchall()
    finally:
        conn.close()


def get_existing_news_description_by_url(url):
    conn = wait_for_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT DESCRIPTION FROM PRIMARY_TABLE WHERE URL=%s LIMIT 1", (url,)
            )
            result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()


def get_primary_article_id_by_url(url):
    conn = wait_for_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT PRIMARY_ARTICLE_ID FROM PRIMARY_TABLE WHERE URL=%s LIMIT 1", (url,)
            )
            result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()


def get_all_rss_embeddings():
    """
    Fetch all article_id, embedding pairs for non-Google RSS articles.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ARTICLE_ID, EMBEDDINGS
            FROM VECTORS_TABLE
            WHERE METADATA NOT LIKE '%google%'
            """
        )
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error fetching RSS embeddings: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_keywords_by_article_id(article_id: str):
    """
    Fetch top 20 keywords for a given article ID.
    """
    conn = wait_for_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT KEYWORD
                FROM KEYWORDS_TABLE
                WHERE ARTICLE_ID = %s
                LIMIT 20;
                """,
                (article_id,),
            )
            results = cursor.fetchall()
        return [row[0] for row in results] if results else []
    finally:
        conn.close()
