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
REG_CHANNEL = -1002739343436  # ID канала для проверки регистраций
DEPOSIT_CHANNEL = -1002690483167  # ID канала для проверки депозитов

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

TEXTS = {
    "start": "🎰 Добро пожаловать в VIP Казино!\n\n🔥 Первые 50 игроков получают +1 бесплатное вращение!\n\n🔹 Для доступа к рулетке:\n1. Зарегистрируйтесь по кнопке ниже\n2. Подтвердите регистрацию\n3. Получите 3 бесплатных вращения",
    "help": "🛠 Инструкция:\n\n1. Используйте новый аккаунт (старые не подойдут)\n2. Если бот не видит регистрацию — подождите 5 минут\n3. Для депозитов используйте только партнерскую ссылку",
    "reg_failed": "❌ Регистрация не найдена!\n\nУбедитесь, что вы:\n1. Создали новый аккаунт\n2. Перешли по ссылке из кнопки «🚀 Зарегистрироваться»",
    "deposit_failed": "⚠️ Депозит не найден!\n\nДля перехода на уровень {level} требуется:\n1. Пополнение от {deposit}₽\n2. Использование партнерской ссылки",
    "vip": "💎 СЕНСАЦИЯ! ВЫ ВЫИГРАЛИ VIP-ДОСТУП!\n\n🔥 Вы вошли в топ-0.1% игроков!\n\nТеперь вам доступно:\n✅ Персональные сигналы\n✅ Эксклюзивные бонусы\n✅ Гарантированные выигрыши"
}

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
        [InlineKeyboardButton(f"🎰 Крутить рулетку ({LEVELS[level]['attempts']} попыток)", web_app=WebAppInfo(url=f"{web_app_url}?level={level}"))],
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

LEVELS = {
    1: {"attempts": 3, "deposit": 0, "text": "🎉 Уровень 1: 3 бесплатных вращения!\n\nВыигрыши до 5000₽!"},
    2: {"attempts": 5, "deposit": 500, "text": "💰 Уровень 2: 5 вращений (депозит от 500₽)"},
    3: {"attempts": 10, "deposit": 2000, "text": "🚀 Уровень 3: 10 вращений (депозит от 2000₽)"},
    4: {"attempts": 15, "deposit": 5000, "text": "🤑 Уровень 4: 15 вращений (депозит от 5000₽)"},
    5: {"attempts": 25, "deposit": 15000, "text": "🏆 Уровень 5: 25 вращений (депозит от 15000₽)"}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(get_start_keyboard())
    if update.message:
        await update.message.reply_photo(
            photo=IMAGES["start"],
            caption=TEXTS["start"],
            reply_markup=keyboard
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
    
    user_id = query.from_user.id
    registered = False
    
    try:
        logger.info(f"🔍 Проверяем регистрацию для user_id: {user_id} в канале {REG_CHANNEL}")
        
        async for msg in context.bot.get_chat_history(chat_id=REG_CHANNEL, limit=100):
            if str(user_id) in msg.text:
                logger.info(f"✅ Найдена регистрация для {user_id} в сообщении: {msg.message_id}")
                registered = True
                break
                
    except Exception as e:
        error_msg = f"❌ Ошибка при проверке регистрации: {str(e)}"
        logger.error(error_msg)
        await query.edit_message_text(
            "⚠️ Ошибка сервера. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ])
        )
        return
    
    if registered:
        await show_level(query, 1)
    else:
        logger.warning(f"❌ Регистрация не найдена для user_id: {user_id}")
        await query.edit_message_text(
            TEXTS["reg_failed"],
            reply_markup=InlineKeyboardMarkup(get_reg_failed_keyboard())
        )

async def show_level(query, level):
    await query.edit_message_media(
        media=InputMediaPhoto(IMAGES[f"level_{level}"], caption=LEVELS[level]["text"]),
        reply_markup=InlineKeyboardMarkup(get_level_keyboard(level))
    )

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level = int(query.data.split('_')[-1])
    
    user_id = query.from_user.id
    deposit_found = False
    
    try:
        required_amount = LEVELS[level]["deposit"]
        async for msg in context.bot.get_chat_history(chat_id=DEPOSIT_CHANNEL, limit=100):
            if str(user_id) in msg.text and f"{required_amount}₽" in msg.text:
                deposit_found = True
                break
    except Exception as e:
        logger.error(f"Ошибка проверки депозита: {e}")
        await query.edit_message_text(
            "⚠️ Ошибка сервера. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_level_{level-1}")]
            ])
        )
        return
    
    if deposit_found:
        await show_level(query, level)
    else:
        await query.edit_message_text(
            TEXTS["deposit_failed"].format(level=level, deposit=LEVELS[level]["deposit"]),
            reply_markup=InlineKeyboardMarkup(get_deposit_failed_keyboard(level))
        )

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    for level in range(1, 6):
        application.add_handler(CallbackQueryHandler(
            lambda update, context, lvl=level: show_level(update.callback_query, lvl),
            pattern=f"^back_to_level_{level}$"
        ))
        application.add_handler(CallbackQueryHandler(
            check_deposit,
            pattern=f"^check_dep_{level}$"
        ))
    
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    if not os.environ.get("BOT_STARTED"):
        os.environ["BOT_STARTED"] = "1"
        threading.Thread(target=self_ping, daemon=True).start()
        threading.Thread(target=app.run, kwargs={'host':'0.0.0.0','port':8080}, daemon=True).start()
        run_bot()
