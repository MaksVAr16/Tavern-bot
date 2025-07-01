import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

# Настройка логов
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PARTNER_URL = "https://1wilib.live/ваша_ссылка"  # Замените!

if not BOT_TOKEN:
    logger.critical("Требуется BOT_TOKEN!")
    raise ValueError("Добавьте BOT_TOKEN в .env")

# Обработчики команд
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="help")]
    ]
    await update.message.reply_text(
        "🎉 Добро пожаловать!\n\n"
        "1. Нажми «Зарегистрироваться»\n"
        "2. Создай НОВЫЙ аккаунт\n"
        "3. Вернись и нажми «Я зарегистрировался»",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_registration(update: Update, context):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "🔍 Проверяем регистрацию...\n\n"
        "Временное сообщение - функционал в разработке"
    )

# Запуск бота
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    
    logger.info("Бот запущен в режиме polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
