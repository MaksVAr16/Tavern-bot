import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from flask import Flask, request

# --- Настройка логов ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Конфиг ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
PARTNER_URL = "https://1wilib.life/v3/aggressive-casino?p=vk3f"
SERVER_URL = "https://tavern-bot.onrender.com"

# --- База данных ---
REGISTERED_USERS_FILE = "registered_users.txt"

# --- Flask для вебхуков ---
app = Flask(__name__)

@app.route('/1win_webhook', methods=['GET'])
def handle_1win_webhook():
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    
    if status == "success":
        with open(REGISTERED_USERS_FILE, 'a') as f:
            f.write(f"{user_id}\n")
        logger.info(f"User {user_id} registered!")
    
    return "OK", 200

# --- Команда /start ---
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="help")]
    ]
    await update.message.reply_text(
        "🎉 Добро пожаловать!\n\n"
        "1. Нажми «Зарегистрироваться»\n"
        "2. Создай НОВЫЙ аккаунт\n"
        "3. Вернись и нажми «Я зарегистрировался»",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- Проверка регистрации ---
async def check_registration(update: Update, context):
    user_id = update.effective_user.id
    
    try:
        with open(REGISTERED_USERS_FILE, 'r') as f:
            if str(user_id) in f.read():
                await update.callback_query.edit_message_text(
                    "✅ Регистрация подтверждена!\n\n"
                    "Теперь вам доступен полный функционал!"
                )
            else:
                await update.callback_query.edit_message_text(
                    "❌ Вы ещё не зарегистрированы!\n\n"
                    "Пройдите регистрацию по кнопке ниже:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)]
                    ])
                )
    except FileNotFoundError:
        await update.callback_query.edit_message_text("⚠️ Ошибка проверки. Попробуйте позже.")

# --- Запуск бота ---
async def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    
    # Отключаем обработку сигналов для Render
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    return bot_app

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

if __name__ == "__main__":
    # Создаём файл для хранения данных
    if not os.path.exists(REGISTERED_USERS_FILE):
        open(REGISTERED_USERS_FILE, 'w').close()
    
    # Запускаем Flask в основном потоке
    from threading import Thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    
    # Запускаем бота в главном потоке
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = loop.run_until_complete(run_bot())
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(bot.stop())
