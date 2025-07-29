import psycopg2
import time
import os
from psycopg2 import OperationalError, Error
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MAX_RETRIES = int(os.getenv("MAX_DB_RETRIES", 5))
RETRY_DELAY = float(os.getenv("RETRY_DELAY_SECONDS", 2))
DB_CONN_TIMEOUT = int(os.getenv("DB_CONN_TIMEOUT", 10))  # Optional timeout (in seconds)


def get_connection():
    try:
        print("🔌 Attempting to connect to the database...")
        return psycopg2.connect(DATABASE_URL, connect_timeout=DB_CONN_TIMEOUT)
    except (OperationalError, Error) as e:
        print(f"❌ Connection attempt failed: {e}")
        return None


def wait_for_connection():
    retries = 0
    conn = None

    while retries < MAX_RETRIES:
        conn = get_connection()
        if conn:
            print("✅ Database connection established.")
            return conn

        retries += 1
        print(f"⏳ Retrying in {RETRY_DELAY} sec... ({retries}/{MAX_RETRIES})")
        time.sleep(RETRY_DELAY)

    raise ConnectionError(
        "❗ Could not connect to the database after multiple retries."
    )
