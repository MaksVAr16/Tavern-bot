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
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен берётся из файла .env
SUPPORT_LINK = "https://t.me/Maksimmm16"  # Ссылка на поддержку
PARTNER_LINK = "https://1wilib.life/?open=register&p=2z3v"  # Партнёрская ссылка
VIP_BOT_LINK = "https://t.me/TESTVIPP_BOT"  # Ссылка на VIP-бота
CHANNEL_LINK = "https://t.me/jacktaverna"  # Ссылка на канал
REG_CHANNEL = -1002739343436  # ID канала регистраций (только цифры!)
DEPOSIT_CHANNEL = -1002690483167  # ID канала депозитов (только цифры!)

# ================== ИЗОБРАЖЕНИЯ ================== #
"""
КАК ЗАМЕНИТЬ ИЗОБРАЖЕНИЯ:
1. Загрузите картинку на imgur.com
2. Возьмите прямую ссылку (оканчивается на .jpg/.png)
3. Вставьте вместо текущих ссылок
"""
IMAGES = {
    "start": "https://i.imgur.com/X8aN0Lk.jpg",  # Для команды /start
    "help": "https://i.imgur.com/X8aN0Lk.jpg",  # Для раздела помощи
    "level_1": "https://i.imgur.com/X8aN0Lk.jpg",  # Для уровня 1
    "level_2": "https://i.imgur.com/X8aN0Lk.jpg",  # Для уровня 2
    "level_3": "https://i.imgur.com/X8aN0Lk.jpg",  # Для уровня 3
    "level_4": "https://i.imgur.com/X8aN0Lk.jpg",  # Для уровня 4
    "level_5": "https://i.imgur.com/X8aN0Lk.jpg",  # Для уровня 5
    "vip": "https://i.imgur.com/X8aN0Lk.jpg"  # Для VIP-сообщения
}

# ================== ТЕКСТЫ СООБЩЕНИЙ ================== """
"""
КАК РЕДАКТИРОВАТЬ ТЕКСТ:
1. Меняйте текст внутри кавычек
2. Для переноса строки используйте \n
3. Для жирного текста - <b>текст</b>
4. Для курсива - <i>текст</i>
"""
TEXTS = {
    "start": (
        "🎰 Добро пожаловать в VIP Казино!\n\n"
        "🔥 Первые 50 игроков получают +1 бесплатное вращение!\n\n"
        "🔹 Для доступа к рулетке:\n"
        "1. Зарегистрируйтесь по кнопке ниже\n"
        "2. Подтвердите регистрацию\n"
        "3. Получите 3 бесплатных вращения"
    ),
    "help": (
        "🛠 Инструкция:\n\n"
        "1. Используйте новый аккаунт (старые не подойдут)\n"
        "2. Если бот не видит регистрацию — подождите 5 минут\n"
        "3. Для депозитов используйте только партнерскую ссылку"
    ),
    "reg_failed": (
        "❌ Регистрация не найдена!\n\n"
        "Убедитесь, что вы:\n"
        "1. Создали новый аккаунт\n"
        "2. Перешли по ссылке из кнопки «🚀 Зарегистрироваться»"
    ),
    "deposit_failed": (
        "⚠️ Депозит не найден!\n\n"
        "Для перехода на уровень {level} требуется:\n"
        "1. Пополнение от {deposit}₽\n"
        "2. Использование партнерской ссылки"
    ),
    "vip": (
        "💎 СЕНСАЦИЯ! ВЫ ВЫИГРАЛИ VIP-ДОСТУП!\n\n"
        "🔥 Вы вошли в топ-0.1% игроков!\n\n"
        "Теперь вам доступно:\n"
        "✅ Персональные сигналы\n"
        "✅ Эксклюзивные бонусы\n"
        "✅ Гарантированные выигрыши"
    )
}

# ================== УРОВНИ И КНОПКИ ================== #
# (остальной код остаётся без изменений)
# ... [здесь идут все ваши функции get_*_keyboard и LEVELS]

# ================== ОСНОВНЫЕ ОБРАБОТЧИКИ ================== #
async def check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    registered = False
    
    try:
        async for msg in context.bot.get_chat_history(chat_id=REG_CHANNEL, limit=100):
            if str(user_id) in msg.text:
                registered = True
                break
    except Exception as e:
        logger.error(f"Ошибка проверки регистрации: {e}")
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
        await query.edit_message_text(
            TEXTS["reg_failed"],
            reply_markup=InlineKeyboardMarkup(get_reg_failed_keyboard()),
            parse_mode="HTML"
        )

async def check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE, level: int):
    query = update.callback_query
    await query.answer()
    
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
            reply_markup=InlineKeyboardMarkup(get_deposit_failed_keyboard(level)),
            parse_mode="HTML"
        )

# ================== ЗАПУСК ================== #
def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Все обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    # Для уровней 2-5
    for level in range(1, 6):
        application.add_handler(CallbackQueryHandler(
            lambda update, context, lvl=level: show_level(update.callback_query, lvl),
            pattern=f"^back_to_level_{level}$"
        ))
        application.add_handler(CallbackQueryHandler(
            lambda update, context, lvl=level: check_deposit(update, context, lvl),
            pattern=f"^check_dep_{lvl}$"
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
