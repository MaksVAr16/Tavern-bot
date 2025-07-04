import os
import logging
import threading
import requests
import time
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# ===== НАСТРОЙКИ =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== SELF-PING =====
def self_ping():
    while True:
        try:
            requests.get("https://ваш-проект.onrender.com")  # Замени на свой URL!
            logger.info("✅ Self-ping выполнен")
        except Exception as e:
            logger.error(f"❌ Ошибка self-ping: {e}")
        time.sleep(240)

app = Flask(__name__)
@app.route('/')
def wake_up():
    return "Бот активен!"

# ===== ПЕРЕМЕННЫЕ =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_LINK = "https://t.me/Maksimmm16"  # Ссылка на менеджера
PARTNER_LINK = "https://1wilib.life/?open=register&p=2z3v"  # Партнерская ссылка
REG_CHANNEL = "@+4T5JdFC8bzBkZmIy"  # Канал с регистрациями

# ===== КЛАВИАТУРЫ =====
def get_start_keyboard():
    """Клавиатура для стартового сообщения (NEW: только регистрация и помощь)"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Зарегистрироваться", url=PARTNER_LINK)],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg")],
        [InlineKeyboardButton("❓ Нужна помощь", callback_data="help")]
    ])

def get_help_keyboard():
    """Клавиатура для раздела 'Помощь' (NEW: менеджер и назад)"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Связаться с менеджером", url=SUPPORT_LINK)],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ])

def get_reg_failed_keyboard():
    """Клавиатура при неудачной проверке регистрации (NEW: помощь и назад)"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ Нужна помощь", callback_data="help")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ])

# ===== ОБРАБОТЧИКИ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет стартовое сообщение с кнопками (NEW: измененная структура)"""
    await update.message.reply_text(
        "🎰 <b>Добро пожаловать!</b>\n\n"
        "Чтобы получить доступ к боту:\n"
        "1. Нажми «🚀 Зарегистрироваться» и создай <b>новый</b> аккаунт\n"
        "2. Подтверди регистрацию кнопкой «✅ Я зарегистрировался»\n\n"
        "Если возникли проблемы — нажми «❓ Нужна помощь»",
        reply_markup=get_start_keyboard(),
        parse_mode="HTML"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Раздел помощи (NEW: добавлена инструкция и кнопки)"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🛠 <b>Инструкция:</b>\n\n"
        "1. Регистрация через кнопку «🚀 Зарегистрироваться» обязательна\n"
        "2. Используйте <b>новый аккаунт</b> (старые не подойдут)\n"
        "3. Если бот не видит регистрацию — попробуйте через 5 минут\n\n"
        "Если проблема осталась — свяжитесь с менеджером:",
        reply_markup=get_help_keyboard(),
        parse_mode="HTML"
    )

async def check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяет регистрацию в канале (NEW: кнопки при неудаче)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    registered = False
    
    # Проверяем последние 100 сообщений в канале
    async for msg in context.bot.get_chat_history(REG_CHANNEL, limit=100):
        if str(user_id) in msg.text:
            registered = True
            break
    
    if registered:
        await query.edit_message_text(
            "🎉 <b>Регистрация подтверждена!</b>\n\n"
            "Теперь вам доступен полный функционал бота.\n"
            "Используйте команды или меню для продолжения.",
            parse_mode="HTML"
        )
    else:
        await query.edit_message_text(
            "❌ <b>Регистрация не найдена!</b>\n\n"
            "Убедитесь, что вы:\n"
            "1. Создали <b>новый</b> аккаунт\n"
            "2. Перешли по ссылке из кнопки «🚀 Зарегистрироваться»\n\n"
            "Если ошибка повторяется — нажмите «❓ Нужна помощь»",
            reply_markup=get_reg_failed_keyboard(),
            parse_mode="HTML"
        )

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в стартовое меню (NEW: добавлен обработчик)"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎰 <b>Добро пожаловать!</b>\n\n"
        "Чтобы получить доступ к боту:\n"
        "1. Нажми «🚀 Зарегистрироваться»\n"
        "2. Подтверди регистрацию кнопкой «✅ Я зарегистрировался»",
        reply_markup=get_start_keyboard(),
        parse_mode="HTML"
    )

# ===== ЗАПУСК =====
def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики (NEW: добавлены help и back_to_start)
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    app_bot.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    app_bot.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    # Критические параметры для избежания конфликтов
    app_bot.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,
        stop_signals=[]
    )

if __name__ == "__main__":
    if not os.environ.get("BOT_STARTED"):
        os.environ["BOT_STARTED"] = "1"
        threading.Thread(target=self_ping, daemon=True).start()
        threading.Thread(target=app.run, kwargs={'host':'0.0.0.0','port':8080}, daemon=True).start()
        run_bot()
