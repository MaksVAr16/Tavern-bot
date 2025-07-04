import os
import logging
import threading
import requests
import time
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Self-ping (для Render Free)
def self_ping():
    while True:
        try:
            requests.get("https://ВАШ_БОТ.onrender.com")  # Замени на свой URL!
            logger.info("✅ Self-ping выполнен")
        except Exception as e:
            logger.error(f"❌ Ошибка self-ping: {e}")
        time.sleep(240)  # Каждые 4 минуты

app = Flask(__name__)
@app.route('/')
def wake_up():
    return "Бот активен!"

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Клавиатуры и обработчики (оставь свои, но убедись, что callback_data совпадает с pattern)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Зарегистрироваться", url="https://1wilib.life/?open=register&p=2z3v")],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg")],
        [InlineKeyboardButton("❓ Нужна помощь", callback_data="help")]
    ]
    await update.message.reply_text(
        "🎰 <b>Добро пожаловать!</b>\n\n"
        "1. Нажми «🚀 Зарегистрироваться»\n"
        "2. Подтверди регистрацию кнопкой ниже",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📞 Менеджер", url="https://t.me/Maksimmm16")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ]
    await query.edit_message_text(
        "🛠 <b>Инструкция:</b>\n\n"
        "1. Регистрация через кнопку обязательна\n"
        "2. Используйте <b>новый</b> аккаунт\n\n"
        "Если ошибка осталась — свяжитесь с менеджером:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(query.message, context)  # Возврат к стартовому сообщению

def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики (убедись, что pattern совпадает с callback_data!)
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    app_bot.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    # Защита от конфликтов
    app_bot.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,
        stop_signals=[]
    )

if __name__ == "__main__":
    # Гарантируем единственный экземпляр
    if not os.environ.get("BOT_STARTED"):
        os.environ["BOT_STARTED"] = "1"
        threading.Thread(target=self_ping, daemon=True).start()
        threading.Thread(target=app.run, kwargs={'host':'0.0.0.0','port':8080}, daemon=True).start()
        run_bot()
