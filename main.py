import os
import logging
import threading
import requests
import time
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Self-ping система
def self_ping():
    while True:
        try:
            requests.get("https://tavern-bot.onrender.com")
        except Exception as e:
            logging.error(f"Self-ping error: {e}")
        time.sleep(240)

# Flask сервер
app = Flask(__name__)
@app.route('/')
def wake_up():
    return "Tavern Bot is alive!"

# Конфигурация бота
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_LINK = "https://t.me/Maksimmm16"
PARTNER_LINK = "https://1wilib.life/?open=register&p=2z3v"
REG_CHANNEL = "@+4T5JdFC8bzBkZmIy"  # Канал для проверки регистрации

# Тексты
TEXTS = {
    "start": (
        "🎰 <b>Добро пожаловать в казино!</b>\n\n"
        "1️⃣ Зарегистрируйся по кнопке ниже\n"
        "2️⃣ Получи 3 бесплатных вращения\n\n"
        "🔥 <i>Первые 50 игроков получают бонус +1 вращение!</i>"
    ),
    "registered": (
        "🎉 <b>Регистрация подтверждена!</b>\n\n"
        "Твои 3 бесплатных вращения готовы!\n\n"
        "⚡ <i>Крути рулетку и забирай призы!</i>"
    )
}

# Универсальная заглушка для изображений
IMAGES = {
    "start": "https://i.ibb.co/7Q78Zy3/test-image.jpg",
    "registered": "https://i.ibb.co/7Q78Zy3/test-image.jpg"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Зарегистрироваться", url=PARTNER_LINK)],
        [InlineKeyboardButton("✅ Проверить регистрацию", callback_data="check_reg")]
    ]
    await update.message.reply_photo(
        photo=IMAGES["start"],
        caption=TEXTS["start"],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async for msg in context.bot.get_chat_history(REG_CHANNEL, limit=100):
        if str(user_id) in msg.text:
            keyboard = [
                [InlineKeyboardButton("🎰 Крутить рулетку (3 попытки)", callback_data="spin")],
                [InlineKeyboardButton("💎 VIP-доступ", url=PARTNER_LINK)]
            ]
            await update.message.reply_photo(
                photo=IMAGES["registered"],
                caption=TEXTS["registered"],
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return
    
    await update.message.reply_text("❌ Ты ещё не зарегистрирован! Нажми /start")

async def spin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prize = "Фриспин 50$"  # Заглушка для теста
    keyboard = [
        [InlineKeyboardButton("🎁 Забрать приз", url=PARTNER_LINK)],
        [InlineKeyboardButton("🔄 Крутить ещё", callback_data="spin")]
    ]
    await update.message.reply_text(
        text=f"🎉 Ты выиграл: {prize}!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.add_handler(CallbackQueryHandler(spin_handler, pattern="^spin$"))
    bot_app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=self_ping, daemon=True).start()
    threading.Thread(target=app.run, kwargs={'host':'0.0.0.0','port':10000}).start()
    run_bot()
