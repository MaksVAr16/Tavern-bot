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
MINI_APP_URL = "https://t.me/Tavern_Rulet_bot/ere"
REGISTERED_USERS_KEY = "REGISTERED_USERS"  # Ключ для хранения ID в переменных Render

app = Flask(__name__)

# Функции для работы с переменными среды
def save_user_id(user_id: str):
    """Сохраняет ID в переменную Render"""
    registered_users = os.getenv(REGISTERED_USERS_KEY, "")
    if user_id not in registered_users.split(","):
        os.environ[REGISTERED_USERS_KEY] = f"{registered_users},{user_id}".strip(",")
        logger.info(f"Юзер {user_id} сохранён")

def is_user_registered(user_id: str) -> bool:
    """Проверяет регистрацию через переменную"""
    registered_users = os.getenv(REGISTERED_USERS_KEY, "")
    return user_id in registered_users.split(",")

async def post_init(app):
    await app.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Предыдущие процессы убиты")

@app.route('/1win_webhook', methods=['GET'])
def handle_webhook():
    try:
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        
        if status == "success" and user_id:
            save_user_id(user_id)  # Используем новую функцию
            logger.info(f"Юзер {user_id} зарегистрирован")
            return "OK", 200
        return "Error", 400
    except Exception as e:
        logger.error(f"Ошибка вебхука: {e}")
        return "Server Error", 500

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

async def check_registration(update: Update, context):
    user_id = str(update.effective_user.id)
    try:
        if is_user_registered(user_id):  # Используем новую функцию
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
        logger.error(f"Ошибка: {e}")
        await update.callback_query.edit_message_text("⚠️ Ошибка сервера")

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

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

async def run_bot():
    bot_app = Application.builder() \
        .token(BOT_TOKEN) \
        .post_init(post_init) \
        .build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    await bot_app.initialize()
    await bot_app.start()
    logger.info("✅ Бот запущен!")
    await bot_app.updater.start_polling()
    return bot_app

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
