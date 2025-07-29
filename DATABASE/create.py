import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def build_DB():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            # Create extensions
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
                conn.commit()
                print("✅ Extensions created (vector, uuid-ossp)")
            except Exception as e:
                print("❌ Error creating extensions:", e)
                conn.rollback()

            # Create PRIMARY_TABLE
            try:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS PRIMARY_TABLE(
                        PRIMARY_ARTICLE_ID UUID PRIMARY KEY,
                        TITLE TEXT NOT NULL,
                        URL TEXT UNIQUE,
                        DESCRIPTION TEXT,
                        NEWS_SOURCE TEXT,
                        PUBLISH_DATE TEXT
                    );
                    """
                )
                conn.commit()
                print("✅ PRIMARY_TABLE created")
            except Exception as e:
                print("❌ Error creating PRIMARY_TABLE:", e)
                conn.rollback()

            # Create SECOND_TABLE
            try:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS SECOND_TABLE (
                        PRIMARY_ARTICLE_ID UUID,
                        ARTICLE_ID UUID PRIMARY KEY,
                        TITLE TEXT NOT NULL,
                        URL TEXT UNIQUE,
                        DESCRIPTION TEXT,
                        PUBLISH_DATE TEXT,
                        ARTICLE_SOURCE TEXT,
                        SCRAPED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        SCRAP_VERSION TEXT
                    );
                    """
                )
                conn.commit()
                print("✅ SECOND_TABLE created")
            except Exception as e:
                print("❌ Error creating SECOND_TABLE:", e)
                conn.rollback()

            # Create VECTORS_TABLE
            try:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS VECTORS_TABLE (
                        ARTICLE_ID UUID PRIMARY KEY,
                        EMBEDDINGS VECTOR(768) NOT NULL,
                        METADATA TEXT UNIQUE NOT NULL
                    );
                    """
                )
                conn.commit()
                print("✅ VECTORS_TABLE created")
            except Exception as e:
                print("❌ Error creating VECTORS_TABLE:", e)
                conn.rollback()

            # Create CATEGORY_TABLE
            try:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS CATEGORY_TABLE (
                        ARTICLE_ID UUID NOT NULL,
                        CATEGORY_ARTICLE_ID UUID PRIMARY KEY NOT NULL,
                        CATEGORY TEXT NOT NULL,
                        SUBCATEGORY TEXT NOT NULL
                    );
                    """
                )
                conn.commit()
                print("✅ CATEGORY_TABLE created")
            except Exception as e:
                print("❌ Error creating CATEGORY_TABLE:", e)
                conn.rollback()

            # Create FULL_NEWS_TABLE
            try:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS FULL_NEWS_TABLE (
                        ARTICLE_ID UUID PRIMARY KEY,
                        TITLE TEXT NOT NULL,
                        FULL_NEWS TEXT NOT NULL
                    );
                    """
                )
                conn.commit()
                print("✅ FULL_NEWS_TABLE created")
            except Exception as e:
                print("❌ Error creating FULL_NEWS_TABLE:", e)
                conn.rollback()

            # Create KEYWORDS_TABLE
            try:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS KEYWORDS_TABLE (
                        ARTICLE_ID UUID NOT NULL,
                        KEYWORD TEXT NOT NULL
                    );
                    """
                )
                conn.commit()
                print("✅ KEYWORDS_TABLE created")
            except Exception as e:
                print("❌ Error creating KEYWORDS_TABLE:", e)
                conn.rollback()

    except Exception as e:
        print("❌ Database connection or setup failed:", e)

    finally:
        if conn:
            conn.close()
            print("🔌 Connection closed")


if __name__ == "__main__":
    build_DB()
