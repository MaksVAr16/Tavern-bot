import os
import logging
import asyncio
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from flask import Flask, request

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфиг
BOT_TOKEN = os.getenv("BOT_TOKEN")
PARTNER_URL = "https://1wilib.life/?open=register&p=2z3v"
SUPPORT_LINK = "https://t.me/Maksimmm16"
REGISTERED_USERS_FILE = os.path.abspath("registered_users.txt")

# Создаем файл если его нет
if not os.path.exists(REGISTERED_USERS_FILE):
    with open(REGISTERED_USERS_FILE, 'w') as f:
        logger.info(f"Создан файл: {REGISTERED_USERS_FILE}")

app = Flask(__name__)

@app.route('/1win_webhook', methods=['GET'])
def handle_webhook():
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    
    if status == "success" and user_id:
        with open(REGISTERED_USERS_FILE, 'a') as f:
            f.write(f"{user_id}\n")
            logger.info(f"Добавлен user_id: {user_id}")
        return "OK", 200
    return "Error", 400

async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg"),
         InlineKeyboardButton("🆘 Помощь", callback_data="help")]
    ]
    text = ("🎉 Добро пожаловать в бота!\n\n"
            "1. Нажми «Зарегистрироваться»\n"
            "2. Создай <b>НОВЫЙ аккаунт</b>\n"
            "3. Вернись и нажми «Я зарегистрировался»")
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def check_registration(update: Update, context):
    user_id = str(update.effective_user.id)
    
    with open(REGISTERED_USERS_FILE, 'r') as f:
        if user_id in f.read():
            await update.callback_query.edit_message_text("✅ <b>Регистрация подтверждена!</b>", parse_mode="HTML")
        else:
            keyboard = [
                [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            await update.callback_query.edit_message_text(
                "❌ <b>Вы ещё не зарегистрированы!</b>",
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
        "2. Используйте ту же ссылку, что и в боте",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def back_to_start(update: Update, context):
    await start(update, context)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

async def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    logger.info("Бот запущен")
    return bot_app

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        bot = loop.run_until_complete(run_bot())
        loop.run_forever()
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
    finally:
        loop.close()
