import os
import logging
import threading
import requests
import time
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# ================== НАСТРОЙКИ ================== #
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def self_ping():
    while True:
        try:
            requests.get("https://tavern-bot.onrender.com")
            logger.info("Self-ping выполнен")
        except Exception as e:
            logger.error(f"Ошибка self-ping: {e}")
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
REG_CHANNEL = -1002739343436
DEPOSIT_CHANNEL = -1002690483167
IMAGE_URL = "https://i.imgur.com/X8aN0Lk.jpg"  # Изображение-заглушка

TEXTS = {
    "start": "🎰 Добро пожаловать в VIP Казино!\n\n🔥 Первые 50 игроков получают +1 бесплатное вращение!\n\n🔹 Для доступа к рулетке:\n1. Зарегистрируйтесь по кнопке ниже\n2. Подтвердите регистрацию\n3. Получите 3 бесплатных вращения",
    "help": "🛠 Инструкция:\n\n1. Используйте новый аккаунт (старые не подойдут)\n2. Если бот не видит регистрацию — подождите 5 минут\n3. Для депозитов используйте только партнерскую ссылку",
    "reg_failed": "❌ Регистрация не найдена!\n\nУбедитесь, что вы:\n1. Создали новый аккаунт\n2. Перешли по ссылке из кнопки «🚀 Зарегистрироваться»\n3. Использовали нового бота, а не старого",
    "deposit_failed": "⚠️ Депозит не найден!\n\nДля перехода на уровень {level} требуется:\n1. Пополнение от {deposit}₽\n2. Использование партнерской ссылки\n3. Совершение депозита с этого аккаунта",
    "vip": "💎 СЕНСАЦИЯ! ВЫ ВЫИГРАЛИ VIP-ДОСТУП!\n\n🔥 Вы вошли в топ-0.1% игроков!\n\nТеперь вам доступно:\n✅ Персональные сигналы\n✅ Эксклюзивные бонусы\n✅ Гарантированные выигрыши",
    "reg_success": "✅ Регистрация подтверждена! Добро пожаловать в VIP Казино!\n\n🎉 Вам доступно 3 бесплатных вращения на Уровне 1!",
    "deposit_success": "✅ Депозит подтвержден! Переходим на Уровень {level}!\n\n🔥 Вам доступно {attempts} вращений!"
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
    await context.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=IMAGE_URL,
        caption=TEXTS["start"],
        reply_markup=InlineKeyboardMarkup(get_start_keyboard())
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=IMAGE_URL,
        caption=TEXTS["help"],
        reply_markup=InlineKeyboardMarkup(get_help_keyboard())
    )

async def check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    try:
        # Временное решение: всегда считаем регистрацию подтвержденной
        # В рабочей версии здесь будет проверка канала
        found = True
        
        if found:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=IMAGE_URL,
                caption=LEVELS[1]["text"],
                reply_markup=InlineKeyboardMarkup(get_level_keyboard(1))
            )
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=TEXTS["reg_failed"],
                reply_markup=InlineKeyboardMarkup(get_reg_failed_keyboard())
            )
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⚠️ Ошибка сервера. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ])
        )

async def check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level = int(query.data.split('_')[-1])
    user_id = query.from_user.id
    deposit = LEVELS[level]["deposit"]
    
    try:
        # Временное решение: всегда считаем депозит подтвержденным
        # В рабочей версии здесь будет проверка канала
        found = True
        
        if found:
            next_level = level + 1 if level < 5 else "vip"
            
            if next_level == "vip":
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=IMAGE_URL,
                    caption=TEXTS["vip"],
                    reply_markup=InlineKeyboardMarkup(get_vip_keyboard()))
            else:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=IMAGE_URL,
                    caption=LEVELS[next_level]["text"],
                    reply_markup=InlineKeyboardMarkup(get_level_keyboard(next_level)))
        else:
            text = TEXTS["deposit_failed"].format(level=level, deposit=deposit)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(get_deposit_failed_keyboard(level)))
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⚠️ Ошибка сервера. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_level_{level-1}")]
            ])
        )

async def back_to_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level = int(query.data.split('_')[-1])
    
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=IMAGE_URL,
        caption=LEVELS[level]["text"],
        reply_markup=InlineKeyboardMarkup(get_level_keyboard(level))
    )

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=IMAGE_URL,
        caption=TEXTS["start"],
        reply_markup=InlineKeyboardMarkup(get_start_keyboard())
    )

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    for level in range(1, 6):
        application.add_handler(CallbackQueryHandler(
            lambda update, ctx, lvl=level: check_deposit(update, ctx, lvl),
            pattern=f"^check_dep_{level}$"
        ))
        
        application.add_handler(CallbackQueryHandler(
            lambda update, ctx, lvl=level: back_to_level(update, ctx, lvl),
            pattern=f"^back_to_level_{level}$"
        ))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    threading.Thread(target=self_ping, daemon=True).start()
    threading.Thread(
        target=app.run, 
        kwargs={'host': '0.0.0.0', 'port': 8080},
        daemon=True
    ).start()
    run_bot()
