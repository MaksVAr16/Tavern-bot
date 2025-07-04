import os
import logging
import threading
import requests
import time
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# ===== КОНФИГУРАЦИЯ =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== SELF-PING (АНТИ-ЗАСЫПАНИЕ) =====
def self_ping():
    while True:
        try:
            requests.get("https://ваш-проект.onrender.com")  # !!! ЗАМЕНИ НА СВОЙ URL !!!
            logger.info("✅ Self-ping выполнен")
        except Exception as e:
            logger.error(f"❌ Ошибка self-ping: {e}")
        time.sleep(240)  # Каждые 4 минуты

# ===== FLASK (ДЛЯ РЕНДЕРА) =====
app = Flask(__name__)
@app.route('/')
def wake_up():
    return "Бот активен!"

# ===== ЗАГРУЗКА ПЕРЕМЕННЫХ =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_LINK = "https://t.me/Maksimmm16"
PARTNER_LINK = "https://1wilib.life/?open=register&p=2z3v"
REG_CHANNEL = "@+4T5JdFC8bzBkZmIy"
DEPOSIT_CHANNEL = "@+Vkx46VQSlTk3ZmYy"

# ===== ОБРАБОТЧИКИ КОМАНД =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Зарегистрироваться", url=PARTNER_LINK)],
        [InlineKeyboardButton("💰 Я пополнил счёт", callback_data="check_deposit")]
    ]
    await update.message.reply_text(
        "🎰 <b>Твой выигрыш уже близко!</b>\n\n"
        "1️⃣ Зарегистрируйся по кнопке ниже\n"
        "2️⃣ Пополни счёт от 500₽\n"
        "3️⃣ Крути рулетку и забирай призы!\n\n"
        "🔥 <i>Первые 10 игроков сегодня получают удвоенный бонус!</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async for msg in context.bot.get_chat_history(REG_CHANNEL, limit=100):
        if str(user_id) in msg.text:
            keyboard = [
                [InlineKeyboardButton("🎰 Крутить рулетку", callback_data="spin")],
                [InlineKeyboardButton("💸 Пополнить счёт", url=PARTNER_LINK)]
            ]
            await update.message.reply_text(
                "🎉 <b>Ты в игре!</b>\n\n"
                "Теперь пополни счёт от 500₽ — и крути рулетку!\n\n"
                "⚡ <i>Сейчас казино даёт бонусы в 2 раза чаще!</i>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return
    await update.message.reply_text("❌ Ты ещё не зарегистрирован!")

async def check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async for msg in context.bot.get_chat_history(DEPOSIT_CHANNEL, limit=100):
        if str(user_id) in msg.text:
            keyboard = [[InlineKeyboardButton("🎡 КРУТИТЬ РУЛЕТКУ", callback_data="spin")]]
            await update.message.reply_text(
                "💰 <b>Твой депозит зачислен!</b>\n\n"
                "Пришло время крутить рулетку и срывать куш!\n\n"
                "🚀 <i>Следующий уровень уже разогрет...</i>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return
    await update.message.reply_text("ℹ️ Пополни счёт от 500₽, чтобы играть!")

async def spin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prize = "Фриспин 50$"
    keyboard = [
        [InlineKeyboardButton("🎁 ЗАБРАТЬ ПРИЗ", callback_data=f"claim_{prize}")],
        [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
    ]
    await update.message.reply_text(
        f"🎁 <b>Ты выиграл: {prize}!</b>\n\n"
        "Этот приз видят только 5% игроков — ты везунчик!\n\n"
        "⏳ <i>Предложение исчезнет через 10 минут...</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ===== ЗАПУСК БОТА (БЕЗ КОНФЛИКТОВ) =====
def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    app_bot.add_handler(CallbackQueryHandler(check_deposit, pattern="^check_deposit$"))
    app_bot.add_handler(CallbackQueryHandler(spin_handler, pattern="^spin$"))
    
    # Критически важные параметры для избежания конфликтов
    app_bot.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,
        stop_signals=[]
    )

if __name__ == "__main__":
    # Гарантируем единственный экземпляр бота
    if not os.environ.get("BOT_STARTED"):
        os.environ["BOT_STARTED"] = "1"
        
        # Запуск self-ping и Flask в фоне
        threading.Thread(target=self_ping, daemon=True).start()
        threading.Thread(target=app.run, kwargs={'host':'0.0.0.0','port':8080}, daemon=True).start()
        
        # Запуск бота
        run_bot()
