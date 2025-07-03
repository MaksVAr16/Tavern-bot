import os
import logging
import asyncio
import psycopg
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
SUPPORT_LINK = "https://t.me/Maksimmm16"
MINI_APP_URL = "https://t.me/Tavern_Rulet_bot/ere"
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)

# Инициализация базы данных
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
                logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")

def save_user_id(user_id: str):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO registered_users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
                    (user_id,)
                )
                conn.commit()
                logger.info(f"✅ Юзер {user_id} сохранён в БД")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения пользователя: {e}")

def is_user_registered(user_id: str) -> bool:
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM registered_users WHERE user_id = %s",
                    (user_id,)
                )
                result = cursor.fetchone() is not None
                logger.info(f"🔍 Проверка регистрации: user_id={user_id}, результат={result}")
                return result
    except Exception as e:
        logger.error(f"❌ Ошибка проверки регистрации: {e}")
        return False

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
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

# Основная функция для запуска бота
async def main():
    # Создаем приложение бота
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info("✅ Бот запущен и готов к работе!")
    
    # Запускаем бота
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    
    # Бесконечный цикл для поддержания работы бота
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
