import psycopg2
import os
from dotenv import load_dotenv
from .getDatabase import wait_for_connection
import uuid
import numpy as np
from datetime import datetime, date

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def insertPrimaryTable(
    PRIMARY_ARTICLE_ID, TITLE, URL, DESCRIPTION, NEWS_SOURCE, PUBLISH_DATE
):
    """Insert data into PRIMARY_TABLE with proper error handling"""
    conn = None
    try:
        conn = wait_for_connection()
        if not conn:
            print("POSTGRE CONNECTION NOT ESTABLISHED")
            return False

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO PRIMARY_TABLE (
                    PRIMARY_ARTICLE_ID,
                    TITLE,
                    URL,
                    DESCRIPTION,
                    NEWS_SOURCE,
                    PUBLISH_DATE
                ) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (URL) DO NOTHING;
                """,
                (
                    PRIMARY_ARTICLE_ID,
                    TITLE,
                    URL,
                    DESCRIPTION,
                    NEWS_SOURCE,
                    PUBLISH_DATE,
                ),
            )
        conn.commit()
        return True

    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        print(f"Database connection error during insertion: {e}")
        print("Attempting to reconnect...")
        conn = wait_for_connection()
        if conn:
            return insertPrimaryTable(
                PRIMARY_ARTICLE_ID, TITLE, URL, DESCRIPTION, NEWS_SOURCE, PUBLISH_DATE
            )
        else:
            print("Failed to reconnect to the database.")
            return False
    except Exception as e:
        print(f"ERROR insertPrimaryTable: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def insertSecondTable(
    PRIMARY_ARTICLE_ID,
    ARTICLE_ID,
    TITLE,
    URL,
    DESCRIPTION,
    PUBLISH_DATE,
    ARTICLE_SOURCE,
    SCRAP_VERSION,
):
    """Insert data into SECOND_TABLE with proper error handling"""
    conn = None
    try:
        conn = wait_for_connection()
        if not conn:
            print("POSTGRE CONNECTION NOT ESTABLISHED")
            return False

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO SECOND_TABLE (
                    PRIMARY_ARTICLE_ID,
                    ARTICLE_ID,
                    TITLE,
                    URL,
                    DESCRIPTION,
                    PUBLISH_DATE,
                    ARTICLE_SOURCE,
                    SCRAPED_DATE,
                    SCRAP_VERSION
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                """,
                (
                    PRIMARY_ARTICLE_ID,
                    ARTICLE_ID,
                    TITLE,
                    URL,
                    DESCRIPTION,
                    PUBLISH_DATE,
                    ARTICLE_SOURCE,
                    SCRAP_VERSION,
                ),
            )
        conn.commit()
        return True

    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        print(f"Database connection error during insertion: {e}")
        print("Attempting to reconnect...")
        conn = wait_for_connection()
        if conn:
            return insertSecondTable(
                PRIMARY_ARTICLE_ID,
                ARTICLE_ID,
                TITLE,
                URL,
                DESCRIPTION,
                PUBLISH_DATE,
                ARTICLE_SOURCE,
                SCRAP_VERSION,
            )
        else:
            print("Failed to reconnect to the database.")
            return False
    except Exception as e:
        print(f"ERROR insertSecondTable: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def insertVECTORSTable(ARTICLE_ID, EMBEDDINGS, METADATA):
    """Insert data into VECTORS_TABLE with proper error handling"""
    conn = None
    try:
        conn = wait_for_connection()
        if not conn:
            print("POSTGRE CONNECTION NOT ESTABLISHED")
            return False

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO VECTORS_TABLE (
                    ARTICLE_ID,
                    EMBEDDINGS,
                    METADATA
                ) VALUES (%s, %s, %s)
                """,
                (ARTICLE_ID, EMBEDDINGS, METADATA),
            )
        conn.commit()
        return True

    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        print(f"Database connection error during insertion: {e}")
        print("Attempting to reconnect...")
        conn = wait_for_connection()
        if conn:
            return insertVECTORSTable(ARTICLE_ID, EMBEDDINGS, METADATA)
        else:
            print("Failed to reconnect to the database.")
            return False
    except Exception as e:
        print(f"ERROR insertVECTORSTable: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def insertCategoryTable(ARTICLE_ID, CATEGORY_ARTICLE_ID, CATEGORY, SUBCATEGORY):
    """Insert data into CATEGORY_TABLE with proper error handling"""
    conn = None
    try:
        conn = wait_for_connection()
        if not conn:
            print("POSTGRE CONNECTION NOT ESTABLISHED")
            return False

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO CATEGORY_TABLE (
                    ARTICLE_ID,
                    CATEGORY_ARTICLE_ID,
                    CATEGORY,
                    SUBCATEGORY
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
                """,
                (ARTICLE_ID, CATEGORY_ARTICLE_ID, CATEGORY, SUBCATEGORY),
            )
        conn.commit()
        return True

    except Exception as e:
        print(f"ERROR insertCategoryTable: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def insertFullNewsTable(ARTICLE_ID, TITLE, FULL_NEWS):
    """Insert data into FULL_NEWS_TABLE with proper error handling"""
    conn = None
    try:
        conn = wait_for_connection()
        if not conn:
            print("POSTGRE CONNECTION NOT ESTABLISHED")
            return False

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO FULL_NEWS_TABLE (
                    ARTICLE_ID,
                    TITLE,
                    FULL_NEWS
                ) VALUES (%s, %s, %s)
                """,
                (ARTICLE_ID, TITLE, FULL_NEWS),
            )
        conn.commit()
        return True

    except Exception as e:
        print(f"ERROR insertFullNewsTable: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def insert_keywords_for_article(article_id, keywords):
    """Insert keywords for an article with proper error handling"""
    conn = None
    try:
        conn = wait_for_connection()
        if not conn:
            print("❌ POSTGRE CONNECTION NOT ESTABLISHED")
            return False

        with conn.cursor() as cursor:
            for keyword in keywords:
                cursor.execute(
                    """
                    INSERT INTO KEYWORDS_TABLE (
                        ARTICLE_ID,
                        KEYWORD
                    ) VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    (article_id, keyword),
                )
        conn.commit()
        return True

    except Exception as e:
        print(f"❌ ERROR insert_keywords_for_article: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def insertUniqueNewsInDB(news, vector_embeddings, article_category, FULL_NEWS):
    """
    Inserts a unique news article and related data into multiple tables using a transaction.
    """
    conn = None
    try:
        conn = wait_for_connection()
        if not conn:
            print("❌ POSTGRE CONNECTION NOT ESTABLISHED")
            return None

        primary_article_id = str(uuid.uuid4())

        # Convert embeddings to list of float32
        embedding_list = (
            vector_embeddings.astype(np.float32).tolist()
            if isinstance(vector_embeddings, np.ndarray)
            else np.array(vector_embeddings, dtype=np.float32).tolist()
        )

        with conn:
            with conn.cursor() as cursor:
                # PRIMARY_TABLE insert
                cursor.execute(
                    """
                    INSERT INTO PRIMARY_TABLE (
                        PRIMARY_ARTICLE_ID, TITLE, URL, DESCRIPTION, NEWS_SOURCE, PUBLISH_DATE
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (URL) DO NOTHING;
                    """,
                    (
                        primary_article_id,
                        news["title"],
                        news["link"],
                        news["description"],
                        news["source"],
                        news["pubDate"],
                    ),
                )

                # SECOND_TABLE insert
                cursor.execute(
                    """
                    INSERT INTO SECOND_TABLE (
                        PRIMARY_ARTICLE_ID, ARTICLE_ID, TITLE, URL, DESCRIPTION,
                        PUBLISH_DATE, ARTICLE_SOURCE, SCRAPED_DATE, SCRAP_VERSION
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                    """,
                    (
                        primary_article_id,
                        primary_article_id,
                        news["title"],
                        news["link"],
                        news["description"],
                        news["pubDate"],
                        news["source"],
                        "SNAP-v1",
                    ),
                )

                # VECTORS_TABLE insert
                cursor.execute(
                    """
                    INSERT INTO VECTORS_TABLE (ARTICLE_ID, EMBEDDINGS, METADATA)
                    VALUES (%s, %s, %s)
                    """,
                    (primary_article_id, embedding_list, news["link"]),
                )

                # FULL_NEWS_TABLE insert
                cursor.execute(
                    """
                    INSERT INTO FULL_NEWS_TABLE (ARTICLE_ID, TITLE, FULL_NEWS)
                    VALUES (%s, %s, %s)
                    """,
                    (primary_article_id, news["title"], FULL_NEWS),
                )

                # KEYWORDS_TABLE insert (optional field)
                keywords = news.get("keywords", [])
                for keyword in keywords:
                    cursor.execute(
                        """
                        INSERT INTO KEYWORDS_TABLE (ARTICLE_ID, KEYWORD)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                        """,
                        (primary_article_id, keyword),
                    )

                # CATEGORY_TABLE insert
                for cat in article_category:
                    category_id = str(uuid.uuid4())
                    cursor.execute(
                        """
                        INSERT INTO CATEGORY_TABLE (
                            ARTICLE_ID, CATEGORY_ARTICLE_ID, CATEGORY, SUBCATEGORY
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING;
                        """,
                        (
                            primary_article_id,
                            category_id,
                            cat.get("category"),
                            cat.get("subcategory"),
                        ),
                    )

        print(f"✅ insertUniqueNewsInDB success for {primary_article_id}")
        return primary_article_id

    except Exception as e:
        print(f"❌ ERROR insertUniqueNewsInDB: {e}")
        if conn:
            conn.rollback()
        return None

    finally:
        if conn:
            conn.close()


def insertDuplicateNewsInDB(
    primary_article_id, news, article_category, vector_embeddings, FULL_NEWS
):
    """Insert duplicate news with all related data using transaction"""
    conn = None
    try:
        conn = wait_for_connection()
        if not conn:
            print("POSTGRE CONNECTION NOT ESTABLISHED")
            return None

        article_id = str(uuid.uuid4())

        # Convert embeddings to proper format
        if isinstance(vector_embeddings, np.ndarray):
            embedding_str = vector_embeddings.astype(np.float32).tolist()
        else:
            embedding_str = np.array(vector_embeddings, dtype=np.float32).tolist()

        # Use transaction for all operations
        with conn:
            with conn.cursor() as cursor:
                # Insert into SECOND_TABLE
                cursor.execute(
                    """
                    INSERT INTO SECOND_TABLE (
                        PRIMARY_ARTICLE_ID, ARTICLE_ID, TITLE, URL, DESCRIPTION,
                        PUBLISH_DATE, ARTICLE_SOURCE, SCRAPED_DATE, SCRAP_VERSION
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                    """,
                    (
                        primary_article_id,
                        article_id,
                        news["title"],
                        news["link"],
                        news["description"],
                        news["pubDate"],
                        news["source"],
                        "SNAP-v1",
                    ),
                )

                # Insert into FULL_NEWS_TABLE
                cursor.execute(
                    """
                    INSERT INTO FULL_NEWS_TABLE (ARTICLE_ID, TITLE, FULL_NEWS)
                    VALUES (%s, %s, %s)
                    """,
                    (article_id, news["title"], FULL_NEWS),
                )

                # Insert keywords
                if "keywords" in news and news["keywords"]:
                    for keyword in news["keywords"]:
                        cursor.execute(
                            """
                            INSERT INTO KEYWORDS_TABLE (ARTICLE_ID, KEYWORD)
                            VALUES (%s, %s) ON CONFLICT DO NOTHING;
                            """,
                            (article_id, keyword),
                        )

                # Insert categories
                for category_obj in article_category:
                    category_id = str(uuid.uuid4())
                    category = category_obj.get("category")
                    subcategory = category_obj.get("subcategory")
                    cursor.execute(
                        """
                        INSERT INTO CATEGORY_TABLE (ARTICLE_ID, CATEGORY_ARTICLE_ID, CATEGORY, SUBCATEGORY)
                        VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;
                        """,
                        (article_id, category_id, category, subcategory),
                    )

        print(f"✅ insertDuplicateNewsInDB success for {article_id}")
        return article_id

    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        print(f"Database connection error during insertion: {e}")
        print("Attempting to reconnect...")
        conn = wait_for_connection()
        if conn:
            return insertDuplicateNewsInDB(
                primary_article_id, news, article_category, vector_embeddings, FULL_NEWS
            )
        else:
            print("Failed to reconnect to the database.")
            return None
    except Exception as e:
        print(f"❌ ERROR insertDuplicateNewsInDB: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()
