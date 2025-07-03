import os
import psycopg
from psycopg import sql
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS registered_users (
                        user_id TEXT PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")

def save_user_id(user_id: str):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO registered_users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
                    (user_id,)
                )
                conn.commit()
                print(f"✅ Юзер {user_id} сохранён в БД")
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")

def is_user_registered(user_id: str) -> bool:
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM registered_users WHERE user_id = %s",
                    (user_id,)
                )
                result = cursor.fetchone() is not None
                print(f"🔍 Проверка регистрации: user_id={user_id}, результат={result}")
                return result
    except Exception as e:
        print(f"❌ Ошибка проверки регистрации: {e}")
        return False