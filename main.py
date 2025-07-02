import os
import logging
import asyncio
import psycopg2
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from flask import Flask, request
from dotenv import load_dotenv

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфиг (все ваши оригинальные настройки)
BOT_TOKEN = os.getenv("BOT_TOKEN")
PARTNER_URL = "https://1wilib.life/?open=register&p=2z3v"
SUPPORT_LINK = "https://t.me/Maksimmm16"
MINI_APP_URL = "https://t.me/Tavern_Rulet_bot/ere"
DATABASE_URL = os.getenv("DATABASE_URL")  # Новый параметр для подключения к Neon

app = Flask(__name__)

# Функции для работы с базой данных (единственное изменение)
def init_db():
    """Инициализация базы данных"""
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
        logger.error(f"Ошибка инициализации БД: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def save_user_id(user_id: str):
    """Сохраняет ID в базу данных"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO registered_users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
                (user_id,)
            )
            conn.commit()
            logger.info(f"Юзер {user_id} сохранён в БД")
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def is_user_registered(user_id: str) -> bool:
    """Проверяет регистрацию в базе данных"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM registered_users WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Ошибка проверки регистрации: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# Инициализация БД при старте
init_db()

# ВСЕ ОСТАЛЬНЫЕ ФУНКЦИИ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ
# (ваши оригинальные функции start, check_registration, help_button, back_to_start и т.д.)
# ... [полный код всех ваших функций без изменений] ...

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_bot())
        loop.run_forever()
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        loop.close()