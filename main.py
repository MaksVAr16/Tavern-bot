import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

# Настройка
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 5000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Полный URL вашего сервиса Render

if not all([BOT_TOKEN, WEBHOOK_URL]):
    raise ValueError("Не заданы BOT_TOKEN или WEBHOOK_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, _):
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url="https://1wilib.life/v3/aggressive-casino?p=vk3f")],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg")]
    ]
    await update.message.reply_text(
        "Добро пожаловать!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_reg(update: Update, _):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🔍 Проверяем регистрацию...")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_reg, pattern="^check_reg$"))

    # Установка вебхука
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
