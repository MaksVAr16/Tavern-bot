import os
import logging
import threading
import requests
import time
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# ===== НАСТРОЙКА ЛОГОВ =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== SELF-PING (ЧТОБЫ БОТ НЕ ЗАСЫПАЛ) =====
def self_ping():
    while True:
        try:
            requests.get("https://ваш-бот.onrender.com")  # ЗАМЕНИ НА СВОЙ URL ПОСЛЕ ДЕПЛОЯ!
            logging.info("✅ Self-ping выполнен")
        except Exception as e:
            logging.error(f"❌ Ошибка self-ping: {e}")
        time.sleep(240)  # Пинг каждые 4 минуты

# ===== FLASK (ДЛЯ ПРОБУЖДЕНИЯ) =====
app = Flask(__name__)
@app.route('/')
def wake_up():
    return "Бот активен!"

# ===== ЗАГРУЗКА ПЕРЕМЕННЫХ =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_LINK = "https://t.me/Maksimmm16"
PARTNER_LINK = "https://1wilib.life/?open=register&p=2z3v"
REG_CHANNEL = "@+4T5JdFC8bzBkZmIy"  # Твой канал регистраций
DEPOSIT_CHANNEL = "@+Vkx46VQSlTk3ZmYy"  # Твой канал депозитов

# ===== ТЕКСТЫ И КНОПКИ =====
TEXTS = {
    "start": (
        "🎰 <b>Твой выигрыш уже близко!</b>\n\n"
        "1️⃣ Зарегистрируйся по кнопке ниже\n"
        "2️⃣ Пополни счёт от 500₽\n"
        "3️⃣ Крути рулетку и забирай призы!\n\n"
        "🔥 <i>Первые 10 игроков сегодня получают удвоенный бонус!</i>"
    ),
    "registered": (
        "🎉 <b>Ты в игре!</b>\n\n"
        "Теперь пополни счёт от 500₽ — и крути рулетку!\n\n"
        "⚡ <i>Сейчас казино даёт бонусы в 2 раза чаще!</i>"
    ),
    "deposit": (
        "💰 <b>Твой депозит зачислен!</b>\n\n"
        "Пришло время крутить рулетку и срывать куш!\n\n"
        "🚀 <i>Следующий уровень уже разогрет...</i>"
    ),
    "prize": (
        "🎁 <b>Ты выиграл: {prize}!</b>\n\n"
        "Этот приз видят только 5% игроков — ты везунчик!\n\n"
        "⏳ <i>Предложение исчезнет через 10 минут...</i>"
    ),
    "vip_prize": (
        "💎 <b>VIP-ДОСТУП АКТИВИРОВАН!</b>\n\n"
        "Ты вошёл в закрытый клуб победителей!\n\n"
        "🔒 <i>Места остались только для 3 игроков...</i>"
    )
}

IMAGES = {
    "start": "https://i.ibb.co/.../start.jpg",  # Замени на реальные URL картинок!
    "registered": "https://i.ibb.co/.../reg.jpg",
    "deposit": "https://i.ibb.co/.../deposit.jpg",
    "prize": "https://i.ibb.co/.../prize.jpg",
    "vip": "https://i.ibb.co/.../vip.jpg"
}

# ===== ОБРАБОТЧИКИ КОМАНД =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Зарегистрироваться", url=PARTNER_LINK)],
        [InlineKeyboardButton("💰 Я пополнил счёт", callback_data="check_deposit")]
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
                [InlineKeyboardButton("🎰 Крутить рулетку", callback_data="spin")],
                [InlineKeyboardButton("💸 Пополнить счёт", url=PARTNER_LINK)]
            ]
            await update.message.reply_photo(
                photo=IMAGES["registered"],
                caption=TEXTS["registered"],
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
            await update.message.reply_photo(
                photo=IMAGES["deposit"],
                caption=TEXTS["deposit"],
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return
    await update.message.reply_text("ℹ️ Пополни счёт от 500₽, чтобы играть!")

async def spin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prize = "Фриспин 50$"  # Здесь можно добавить логику рулетки
    keyboard = [
        [InlineKeyboardButton("🎁 ЗАБРАТЬ ПРИЗ", callback_data=f"claim_{prize}")],
        [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
    ]
    await update.message.reply_photo(
        photo=IMAGES["prize"],
        caption=TEXTS["prize"].format(prize=prize),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ===== ЗАПУСК БОТА =====
def main():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    app_bot.add_handler(CallbackQueryHandler(check_deposit, pattern="^check_deposit$"))
    app_bot.add_handler(CallbackQueryHandler(spin_handler, pattern="^spin$"))
    
    app_bot.run_polling()

if __name__ == "__main__":
    # Запускаем self-ping и Flask в фоне
    threading.Thread(target=self_ping, daemon=True).start()
    threading.Thread(target=app.run, kwargs={'host':'0.0.0.0','port':8080}, daemon=True).start()
    
    # Запускаем бота
    main()
