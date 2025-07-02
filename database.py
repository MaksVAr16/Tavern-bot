import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registered_users (
                    user_id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def save_user_id(user_id: str):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO registered_users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
                (user_id,)
            )
            conn.commit()
    except Exception as e:
        print(f"Save error: {e}")
    finally:
        if conn:
            conn.close()

def is_user_registered(user_id: str) -> bool:
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM registered_users WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        print(f"Check error: {e}")
        return False
    finally:
        if conn:
            conn.close()