import os
import logging
import asyncio
from threading import Thread, Lock
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from flask import Flask, request

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
REGISTERED_USERS_FILE = "registered_users.txt"
file_lock = Lock()  # Для безопасной записи в файл

# --- Flask для вебхуков ---
app = Flask(__name__)

@app.route('/1win_webhook', methods=['GET', 'POST'])
def handle_1win_webhook():
    try:
        # Получаем параметры
        user_id = request.args.get('user_id') or (request.json and request.json.get('user_id'))
        status = request.args.get('status') or (request.json and request.json.get('status'))
        
        if not user_id:
            return "user_id required", 400
        
        # Логируем запрос
        logger.info(f"Получен запрос: user_id={user_id}, status={status}")
        
        if status == "success":
            with file_lock:
                # Проверяем, не зарегистрирован ли уже пользователь
                registered = False
                if os.path.exists(REGISTERED_USERS_FILE):
                    with open(REGISTERED_USERS_FILE, 'r') as f:
                        registered = str(user_id) in f.read()
                
                if not registered:
                    with open(REGISTERED_USERS_FILE, 'a') as f:
                        f.write(f"{user_id}\n")
                    logger.info(f"Успешная регистрация: {user_id}")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return "Server Error", 500

# --- Все ваши обработчики сообщений и кнопок БЕЗ ИЗМЕНЕНИЙ ---
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

async def help_button(update: Update, context):
    await update.callback_query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")],
        [InlineKeyboardButton("📞 Написать оператору", url=SUPPORT_LINK)]
    ]
    
    await update.callback_query.edit_message_text(
        "🛠 <b>Центр помощи</b>\n\n"
        "Если у вас проблемы с регистрацией:\n"
        "1. Обязательно создавайте <b>новый аккаунт</b>\n"
        "2. Используйте ту же ссылку, что и в боте\n"
        "3. Если не получается - напишите нашему оператору",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def check_registration(update: Update, context):
    user_id = update.effective_user.id
    
    try:
        with open(REGISTERED_USERS_FILE, 'r') as f:
            if str(user_id) in f.read():
                await update.callback_query.edit_message_text(
                    "✅ <b>Регистрация подтверждена!</b>\n\n"
                    "Теперь вам доступен полный функционал!",
                    parse_mode="HTML"
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
                ]
                
                await update.callback_query.edit_message_text(
                    "❌ <b>Вы ещё не зарегистрированы!</b>\n\n"
                    "Пройдите регистрацию по кнопке ниже:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="HTML"
                )
    except FileNotFoundError:
        await update.callback_query.edit_message_text("⚠️ Ошибка проверки. Попробуйте позже.")

async def back_to_start(update: Update, context):
    await start(update, context)

# --- Запуск ---
async def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    return bot_app

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

if __name__ == "__main__":
    # Создаем файл если его нет
    if not os.path.exists(REGISTERED_USERS_FILE):
        with open(REGISTERED_USERS_FILE, 'w') as f:
            f.write("")
    
    # Запускаем Flask в фоне
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем бота
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        bot = loop.run_until_complete(run_bot())
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(bot.stop())
    finally:
        loop.close()
