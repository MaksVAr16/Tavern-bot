import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

# ===== НАСТРОЙКА =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 5000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL вашего Render-сервиса

# Проверка переменных
if not all([BOT_TOKEN, WEBHOOK_URL]):
    raise ValueError("❌ Не заданы BOT_TOKEN или WEBHOOK_URL!")

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== ОБРАБОТЧИКИ КОМАНД =====
async def start(update: Update, _):
    """Приветственное сообщение с кнопками"""
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url="https://1wilib.life/v3/aggressive-casino?p=vk3f")],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg")],
        [InlineKeyboardButton("🆘 Нужна помощь", callback_data="help")]
    ]
    
    await update.message.reply_text(
        "🎰 <b>Добро пожаловать в CasinoBot!</b>\n\n"
        "Чтобы получить доступ:\n"
        "1. Нажми «Зарегистрироваться»\n"
        "2. Создай <b>НОВЫЙ</b> аккаунт\n"
        "3. Подтверди регистрацию кнопкой ниже\n\n"
        "💰 Бонус: 1000 кредитов новым игрокам!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def check_registration(update: Update, _):
    """Проверка регистрации (заглушка)"""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "🔍 <b>Проверяем вашу регистрацию...</b>\n\n"
        "Это тестовое сообщение. Реальный функционал добавим позже.",
        parse_mode="HTML"
    )

async def help_command(update: Update, _):
    """Обработчик кнопки помощи"""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "📌 <b>Помощь по боту</b>\n\n"
        "1. Регистрация обязательна для доступа\n"
        "2. Используйте только <b>новый аккаунт</b>\n"
        "3. Проблемы? Пишите: @Maksimmm16\n\n"
        "<i>Ответим в течение 5 минут!</i>",
        parse_mode="HTML"
    )

# ===== ЗАПУСК =====
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    app.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    
    # Вебхук
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
