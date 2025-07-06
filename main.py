import os
import logging
import threading
import requests
import time
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# ================== НАСТРОЙКИ ================== #
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Self-ping для Render
def self_ping():
    while True:
        try:
            requests.get("https://tavern-bot.onrender.com")
            logger.info("✅ Self-ping выполнен")
        except Exception as e:
            logger.error(f"❌ Ошибка self-ping: {e}")
        time.sleep(240)

app = Flask(__name__)
@app.route('/')
def wake_up():
    return "Бот активен!"

# ================== КОНФИГУРАЦИЯ ================== #
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_LINK = "https://t.me/Maksimmm16"
PARTNER_LINK = "https://1wilib.life/?open=register&p=2z3v"
VIP_BOT_LINK = "https://t.me/TESTVIPP_BOT"
CHANNEL_LINK = "https://t.me/jacktaverna"
REG_CHANNEL = "-1002739343436"  # Важно: только цифры
DEPOSIT_CHANNEL = "-1002690483167"

# Изображения (рабочие ссылки)
IMAGES = {
    "start": "https://i.imgur.com/X8aN0Lk.jpg",
    "help": "https://i.imgur.com/X8aN0Lk.jpg", 
    "level_1": "https://i.imgur.com/X8aN0Lk.jpg",
    "level_2": "https://i.imgur.com/X8aN0Lk.jpg",
    "level_3": "https://i.imgur.com/X8aN0Lk.jpg",
    "level_4": "https://i.imgur.com/X8aN0Lk.jpg",
    "level_5": "https://i.imgur.com/X8aN0Lk.jpg",
    "vip": "https://i.imgur.com/X8aN0Lk.jpg"
}

# Тексты сообщений (полностью сохранены)
TEXTS = {
    "start": (
        "🎰 <b>Добро пожаловать в VIP Казино!</b>\n\n"
        "🔥 <i>Первые 50 игроков получают +1 бесплатное вращение!</i>\n\n"
        "🔹 Для доступа к рулетке:\n"
        "1. Зарегистрируйтесь по кнопке ниже\n"
        "2. Подтвердите регистрацию\n"
        "3. Получите 3 бесплатных вращения"
    ),
    "help": (
        "🛠 <b>Инструкция:</b>\n\n"
        "1. Используйте <b>новый аккаунт</b> (старые не подойдут)\n"
        "2. Если бот не видит регистрацию — подождите 5 минут\n"
        "3. Для депозитов используйте только партнерскую ссылку"
    ),
    "reg_failed": (
        "❌ <b>Регистрация не найдена!</b>\n\n"
        "Убедитесь, что вы:\n"
        "1. Создали <b>новый</b> аккаунт\n"
        "2. Перешли по ссылке из кнопки «🚀 Зарегистрироваться»"
    ),
    "deposit_failed": (
        "⚠️ <b>Депозит не найден!</b>\n\n"
        "Для перехода на уровень {level} требуется:\n"
        "1. Пополнение от {deposit}₽\n"
        "2. Использование партнерской ссылки"
    ),
    "vip": (
        "💎 <b>СЕНСАЦИЯ! ВЫ ВЫИГРАЛИ VIP-ДОСТУП!</b>\n\n"
        "🔥 <i>Вы вошли в топ-0.1% игроков!</i>\n\n"
        "Теперь вам доступно:\n"
        "✅ Персональные сигналы\n"
        "✅ Эксклюзивные бонусы\n"
        "✅ Гарантированные выигрыши"
    )
}

# Клавиатуры (полностью сохранены)
def get_start_keyboard():
    return [
        [InlineKeyboardButton("🚀 Зарегистрироваться", url=PARTNER_LINK)],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg")],
        [InlineKeyboardButton("❓ Нужна помощь", callback_data="help")]
    ]

def get_help_keyboard():
    return [
        [InlineKeyboardButton("📞 Менеджер", url=SUPPORT_LINK)],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ]

def get_reg_failed_keyboard():
    return [
        [InlineKeyboardButton("🔄 Попробовать снова", url=PARTNER_LINK)],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
    ]

def get_level_keyboard(level):
    web_app_url = "https://your-webapp.com/roulette"
    return [
        [InlineKeyboardButton(
            f"🎰 Крутить рулетку ({LEVELS[level]['attempts']} попыток)",
            web_app=WebAppInfo(url=f"{web_app_url}?level={level}")
        )],
        [InlineKeyboardButton("💎 VIP-доступ", url=PARTNER_LINK)],
        [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
    ]

def get_deposit_failed_keyboard(level):
    return [
        [InlineKeyboardButton("💳 Пополнить баланс", url=PARTNER_LINK)],
        [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_dep_{level}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_level_{level-1}" if level > 1 else "back_to_start")]
    ]

def get_vip_keyboard():
    return [
        [InlineKeyboardButton("💎 Получить VIP", url=PARTNER_LINK)],
        [InlineKeyboardButton("🎁 Забрать приз", url=VIP_BOT_LINK)],
        [InlineKeyboardButton("📢 Наш канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
    ]

# Уровни (полностью сохранены)
LEVELS = {
    1: {"attempts": 3, "deposit": 0, "text": "🎉 <b>Уровень 1: 3 бесплатных вращения!</b>\n\nВыигрыши до <b>5000₽</b>!"},
    2: {"attempts": 5, "deposit": 500, "text": "💰 <b>Уровень 2: 5 вращений (депозит от 500₽)</b>"},
    3: {"attempts": 10, "deposit": 2000, "text": "🚀 <b>Уровень 3: 10 вращений (депозит от 2000₽)</b>"},
    4: {"attempts": 15, "deposit": 5000, "text": "🤑 <b>Уровень 4: 15 вращений (депозит от 5000₽)</b>"},
    5: {"attempts": 25, "deposit": 15000, "text": "🏆 <b>Уровень 5: 25 вращений (депозит от 15000₽)</b>"}
}

# ================== ОБРАБОТЧИКИ ================== #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(get_start_keyboard())
    if update.message:
        await update.message.reply_photo(
            photo=IMAGES["start"],
            caption=TEXTS["start"],
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_media(
            media=InputMediaPhoto(IMAGES["start"], caption=TEXTS["start"]),
            reply_markup=keyboard
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_media(
        media=InputMediaPhoto(IMAGES["help"], caption=TEXTS["help"]),
        reply_markup=InlineKeyboardMarkup(get_help_keyboard())
    )

async def check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Тестовая версия - всегда успешная регистрация
    await show_level(query, 1)

async def show_level(query, level):
    await query.edit_message_media(
        media=InputMediaPhoto(IMAGES[f"level_{level}"], caption=LEVELS[level]["text"]),
        reply_markup=InlineKeyboardMarkup(get_level_keyboard(level))
    )

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ================== ЗАПУСК ================== #
def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Все обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    # Для уровней 2-5 (заглушки)
    for level in range(1, 6):
        application.add_handler(CallbackQueryHandler(
            lambda update, context, lvl=level: show_level(update.callback_query, lvl),
            pattern=f"^back_to_level_{level}$"
        ))
        application.add_handler(CallbackQueryHandler(
            lambda update, context, lvl=level: check_deposit(update, context, lvl),
            pattern=f"^check_dep_{level}$"
        ))
    
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,
        drop_pending_updates=True
    )

# Заглушка для проверки депозита
async def check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE, level: int):
    query = update.callback_query
    await query.answer()
    await show_level(query, level)

if __name__ == "__main__":
    if not os.environ.get("BOT_STARTED"):
        os.environ["BOT_STARTED"] = "1"
        threading.Thread(target=self_ping, daemon=True).start()
        threading.Thread(target=app.run, kwargs={'host':'0.0.0.0','port':8080}, daemon=True).start()
        run_bot()
