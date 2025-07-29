import psycopg2
import os
from dotenv import load_dotenv
from .getDatabase import wait_for_connection

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

allowed_columns = {
    "PRIMARY_TABLE": [
        "PRIMARY_ARTICLE_ID",
        "ARTICLE_ID",
        "TITLE",
        "URL",
        "DESCRIPTION",
        "NEWS_SOURCE",
        "PUBLISH_DATE",
    ],
    "SECOND_TABLE": [
        "PRIMARY_ARTICLE_ID",
        "ARTICLE_ID",
        "TITLE",
        "URL",
        "DESCRIPTION",
        "PUBLISH_DATE",
        "PUBLISH_TIME",
        "ARTICLE_SOURCE",
        "SCRAP_VERSION",
    ],
    "VECTORS_TABLE": ["ARTICLE_ID", "EMBEDDINGS", "METADATA"],
    "CATEGORY_TABLE": ["ARTICLE_ID", "SOURCE_ARTICLE_ID", "SOURCE"],
    "KEYWORDS_TABLE": [
        "ARTICLE_ID",
        "KEYWORD",
    ],
}


def if_unique_data(table: str, column: str, value):
    if table not in allowed_columns:
        raise ValueError(f"Table '{table}' is not allowed.")

    if column not in allowed_columns[table]:
        raise ValueError(f"Column '{column}' not allowed in table '{table}'.")

    query = f"""
        SELECT 1 FROM {table}
        WHERE {column} = %s
        LIMIT 1;
    """

    cursor.execute(query, (value,))
    value_exist = cursor.fetchone()
    return not value_exist


def HideFilteredResults(table: str, column: str, value):
    if table not in allowed_columns:
        raise ValueError(f"Table '{table}' is not allowed.")

    if column not in allowed_columns[table]:
        raise ValueError(f"Column '{column}' not allowed in table '{table}'.")

    query = f"""
        SELECT * FROM {table}
        WHERE {column} != %s
    """

    cursor.execute(query, (value,))
    return cursor.fetchall()


def ShowFilteredResults(table: str, column: str, value):
    if table not in allowed_columns:
        raise ValueError(f"Table '{table}' is not allowed.")

    if column not in allowed_columns[table]:
        raise ValueError(f"Column '{column}' not allowed in table '{table}'.")

    query = f"""
        SELECT * FROM {table}
        WHERE {column} = %s
    """

    cursor.execute(query, (value,))
    return cursor.fetchall()


def get_existing_news_description_by_url(url):
    conn = wait_for_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT DESCRIPTION FROM PRIMARY_TABLE WHERE URL=%s LIMIT 1", (url,)
        )
        result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_primary_article_id_by_url(url):
    conn = wait_for_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT PRIMARY_ARTICLE_ID FROM PRIMARY_TABLE WHERE URL=%s LIMIT 1", (url,)
        )
        result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_all_rss_embeddings():
    """
    Fetches all (article_id, embedding) for RSS articles from VECTORS_TABLE.
    RSS news is identified by filtering out Google-based metadata URLs.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Adjust this logic based on how you distinguish RSS vs Google articles.
        # Here, we assume Google articles have "google" in the metadata URL.
        cursor.execute(
            """
            SELECT ARTICLE_ID, EMBEDDINGS
            FROM VECTORS_TABLE
            WHERE METADATA NOT LIKE '%google%'  -- assuming google urls contain 'google'
        """
        )
        results = cursor.fetchall()

        return results  # List of (UUID, pgvector)
    except Exception as e:
        print(f"Error fetching RSS embeddings: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_keywords_by_article_id(article_id: str):
    """
    Fetch top 20 keywords for a given article ID from keyword table.
    Returns a list of keywords.
    """
    conn = wait_for_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT KEYWORD
            FROM keyword
            WHERE ARTICLE_ID = %s
            LIMIT 20;
            """,
            (article_id,),
        )
        result = cursor.fetchall()
    conn.close()
    return [row[0] for row in result] if result else []
