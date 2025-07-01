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
SUPPORT_LINK = "https://t.me/Maksimmm16"
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

# --- Улучшенная команда /start ---
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
        [
            InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg"),
            InlineKeyboardButton("🆘 Помощь", callback_data="help")
        ]
    ]
    
    # Если это callback (нажатие кнопки "Назад")
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
        # Если это команда /start
        await update.message.reply_text(
            "🎉 Добро пожаловать в бота!\n\n"
            "1. Нажми «Зарегистрироваться»\n"
            "2. Создай <b>НОВЫЙ аккаунт</b> (вход в существующий не подойдёт!)\n"
            "3. Вернись и нажми «Я зарегистрировался»\n\n"
            "Если возникли проблемы - нажми «Помощь»",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

# --- Обработчик кнопки помощи ---
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

# --- Проверка регистрации ---
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

# --- Обработчик кнопки "Назад" ---
async def back_to_start(update: Update, context):
    await start(update, context)  # Используем ту же функцию start, но для callback

# --- Запуск бота ---
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
    if not os.path.exists(REGISTERED_USERS_FILE):
        open(REGISTERED_USERS_FILE, 'w').close()
    
    from threading import Thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = loop.run_until_complete(run_bot())
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(bot.stop())
