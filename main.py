import os
import logging
import asyncio
from threading import Thread, Lock
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from flask import Flask, request, jsonify

# --- Настройка логов ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Конфиг ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
PARTNER_URL = "https://1wilib.life/?open=register&p=2z3v"
SUPPORT_LINK = "https://t.me/Maksimmm16"
SERVER_URL = "https://tavern-bot.onrender.com"

# --- База данных ---
REGISTERED_USERS_FILE = os.path.abspath("registered_users.txt")
file_lock = Lock()

# --- Создаем Flask приложение ---
app = Flask(__name__)

@app.route('/1win_webhook', methods=['GET', 'POST'])
def handle_1win_webhook():
    try:
        logger.info(f"Получен запрос: {request.method} {request.url}")
        
        # Получаем параметры
        user_id = request.args.get('user_id') or (request.json and request.json.get('user_id'))
        status = request.args.get('status') or (request.json and request.json.get('status'))
        
        if not user_id:
            logger.error("Отсутствует user_id")
            return jsonify({"status": "error", "message": "user_id required"}), 400
        
        logger.info(f"Обработка: user_id={user_id}, status={status}")

        # Гарантируем существование файла
        if not os.path.exists(REGISTERED_USERS_FILE):
            with open(REGISTERED_USERS_FILE, 'w') as f:
                logger.info(f"Создан новый файл: {REGISTERED_USERS_FILE}")
        
        if status == "success":
            with file_lock:
                with open(REGISTERED_USERS_FILE, 'a+') as f:
                    f.seek(0)
                    if str(user_id) not in f.read():
                        f.write(f"{user_id}\n")
                        logger.info(f"Успешная регистрация: {user_id}")
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Ошибка вебхука: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Все ваши обработчики сообщений (оставляем без изменений) ---
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
        [
            InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg"),
            InlineKeyboardButton("🆘 Помощь", callback_data="help")
        ]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🎉 Добро пожаловать в бота!\n\n"
            "1. Нажми «Зарегистрироваться»\n"
            "2. Создай <b>НОВЫЙ аккаунт</b> (вход в существующий не подойдёт!)\n"
            "3. Вернись и нажми «Я зарегистрировался»\n\n"
            "Если возникли проблемы - нажми «Помощь»",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "🎉 Добро пожаловать в бота!\n\n"
            "1. Нажми «Зарегистрироваться»\n"
            "2. Создай <b>НОВЫЙ аккаунт</b> (вход в существующий не подойдёт!)\n"
            "3. Вернись и нажми «Я зарегистрировался»\n\n"
            "Если возникли проблемы - нажми «Помощь»",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

# ... (остальные обработчики без изменений) ...

# --- Запуск Flask ---
def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

# --- Запуск бота ---
async def run_bot():
    # Гарантируем существование файла
    if not os.path.exists(REGISTERED_USERS_FILE):
        with open(REGISTERED_USERS_FILE, 'w') as f:
            logger.info(f"Создан файл при запуске: {REGISTERED_USERS_FILE}")
    
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    logger.info("Бот успешно запущен")
    return bot_app

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Настраиваем и запускаем бота
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        bot = loop.run_until_complete(run_bot())
        loop.run_forever()
    except Exception as e:
        logger.error(f"Ошибка запуска: {str(e)}")
    finally:
        loop.close()
