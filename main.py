import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from flask import Flask, request, send_file
from threading import Thread

# --- Настройка логов ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Конфиг ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
PARTNER_URL = "https://1wilib.life/v3/aggressive-casino?p=vk3f"  # Ваша партнёрская ссылка
SERVER_URL = "https://tavern-bot.onrender.com"  # Ваш URL на Render

# --- Базы данных (файлы) ---
REGISTERED_USERS_FILE = "registered_users.txt"
DEPOSITED_USERS_FILE = "deposited_users.txt"

# --- Flask для вебхуков и рулетки ---
app = Flask(__name__)

@app.route('/1win_webhook', methods=['GET'])
def handle_1win_webhook():
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    deposit_amount = request.args.get('deposit_amount')
    
    if status == "success":
        # Запись регистрации
        with open(REGISTERED_USERS_FILE, 'a') as f:
            f.write(f"{user_id}\n")
        logger.info(f"User {user_id} registered!")
        
        # Запись депозита (если есть)
        if deposit_amount and int(deposit_amount) >= 500:
            with open(DEPOSITED_USERS_FILE, 'a') as f:
                f.write(f"{user_id}\n")
            logger.info(f"User {user_id} deposited {deposit_amount} RUB!")
    
    return "OK", 200

@app.route('/roulette')
def roulette():
    return send_file('templates/roulette.html')

# --- Команда /start ---
async def start(update: Update, context):
    user_id = update.effective_user.id
    
    # Проверяем, есть ли депозит
    deposited = False
    if os.path.exists(DEPOSITED_USERS_FILE):
        with open(DEPOSITED_USERS_FILE, 'r') as f:
            deposited = str(user_id) in f.read()
    
    # Кнопки
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg")]
    ]
    
    if deposited:
        keyboard.append([InlineKeyboardButton("🎰 Крутить рулетку", url=f"{SERVER_URL}/roulette")])
    
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
def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.run_polling()

if __name__ == "__main__":
    # Создаём файлы для хранения данных, если их нет
    for file in [REGISTERED_USERS_FILE, DEPOSITED_USERS_FILE]:
        if not os.path.exists(file):
            open(file, 'w').close()
    
    # Запускаем бота и Flask в отдельных потоках
    Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
