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

# Конфиг
BOT_TOKEN = os.getenv("BOT_TOKEN")
PARTNER_URL = "https://1wilib.life/?open=register&p=2z3v"
SUPPORT_LINK = " https://t.me/Maksimmm16 "
MINI_APP_URL = "https://t.me/Tavern_Rulet_bot/ere "
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.warning("⚠️ DATABASE_URL не найдена в .env!")

app = Flask(__name__)

# Инициализация базы данных
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
            logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def save_user_id(user_id: str):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            logger.info(f"💾 Сохраняю user_id={user_id} в БД")
            cursor.execute(
                "INSERT INTO registered_users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
                (user_id,)
            )
            conn.commit()
            logger.info(f"✅ Юзер {user_id} сохранён в БД")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения пользователя: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def is_user_registered(user_id: str) -> bool:
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            logger.info(f"🔍 Проверяю регистрацию для user_id={user_id}")
            cursor.execute(
                "SELECT 1 FROM registered_users WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone() is not None
            logger.info(f"🔍 Результат проверки регистрации: {result}")
            return result
    except Exception as e:
        logger.error(f"❌ Ошибка проверки регистрации: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


# Инициализация БД при старте
init_db()


# Вебхук для регистрации
@app.route('/1win_webhook', methods=['GET'])
def handle_webhook():
    try:
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        logger.info(f"🔄 Вебхук получен: user_id={user_id}, status={status}")

        if status == "success" and user_id:
            save_user_id(user_id)
            logger.info(f"✅ Юзер {user_id} зарегистрирован")
            return "OK", 200
        else:
            logger.warning(f"🚫 Получен невалидный вебхук: {request.url}")
            return "Error", 400
    except Exception as e:
        logger.error(f"❌ Ошибка вебхука: {e}")
        return "Server Error", 500


# Команда /start
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
        [
            InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg"),
            InlineKeyboardButton("❓ Нужна помощь", callback_data="help")
        ]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🎰 <b>Ты уже на полпути к победе...</b>\n\n"
            "1. Нажми «Зарегистрироваться»\n"
            "2. Создай <b>НОВЫЙ аккаунт</b>\n"
            "3. Нажми «Я зарегистрировался»",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "🎰 <b>Ты уже на полпути к победе...</b>\n\n"
            "1. Нажми «Зарегистрироваться»\n"
            "2. Создай <b>НОВЫЙ аккаунт</b>\n"
            "3. Нажми «Я зарегистрировался»",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )


# Проверка регистрации
async def check_registration(update: Update, context):
    user_id = str(update.effective_user.id)
    try:
        logger.info(f"🕵️ Проверяю регистрацию для Telegram user_id={user_id}")
        if is_user_registered(user_id):
            keyboard = [
                [InlineKeyboardButton("🎰 Перейти к рулетке", url=MINI_APP_URL)],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            text = "🎉 <b>Регистрация подтверждена!</b>"
        else:
            keyboard = [
                [InlineKeyboardButton("🔹 Попробовать ещё раз", url=PARTNER_URL)],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            text = "❌ <b>Регистрация не найдена!</b>"
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка проверки регистрации: {e}")
        await update.callback_query.edit_message_text("⚠️ Ошибка сервера")


# Кнопка помощи
async def help_button(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")],
        [InlineKeyboardButton("📞 Менеджер", url=SUPPORT_LINK)]
    ]
    await update.callback_query.edit_message_text(
        "🛠 <b>Центр помощи</b>\n\n"
        "Для связи с менеджером:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# Назад в начало
async def back_to_start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
        [
            InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg"),
            InlineKeyboardButton("❓ Нужна помощь", callback_data="help")
        ]
    ]
    await update.callback_query.edit_message_text(
        "🎰 <b>Ты уже на полпути к победе...</b>\n\n"
        "1. Нажми «Зарегистрироваться»\n"
        "2. Создай <b>НОВЫЙ аккаунт</b>\n"
        "3. Нажми «Я зарегистрировался»",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# Запуск Flask
def run_flask():
    port = int(os.getenv('PORT', 10000))
    logger.info(f"🔌 Запускаю Flask на порту {port}")
    app.run(host='0.0.0.0', port=port)


# Запуск бота
async def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))

    logger.info("✅ Бот запущен и готов к работе!")
    await bot_app.run_polling()


if __name__ == "__main__":
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    try:
        asyncio.run(run_bot())
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
