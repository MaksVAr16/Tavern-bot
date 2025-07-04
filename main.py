import os
import logging
import threading
import requests
import time
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

# Self-ping для Render
def self_ping():
    while True:
        try:
            requests.get("https://ВАШ_БОТ.onrender.com")  # Замените на свой URL!
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
VIP_BOT_LINK = "https://t.me/your_vip_bot"  # Замените на ссылку VIP-бота
CHANNEL_LINK = "https://t.me/your_channel"  # Замените на ссылку канала
REG_CHANNEL = "@+4T5JdFC8bzBkZmIy"  # Канал проверки регистрации
DEPOSIT_CHANNEL = "@ваш_канал_депозитов"  # Канал проверки депозитов

# ================== ТЕКСТЫ ================== #
LEVELS = {
    1: {
        "text": (
            "🎰 <b>Уровень 1: 3 бесплатных вращения!</b>\n\n"
            "🔥 <i>Только сегодня - бонусные коэффициенты!</i>\n\n"
            "Выигрыши до <b>5000₽</b> без вложений!"
        ),
        "attempts": 3,
        "deposit": 0,
        "next_level_text": "Для перехода на Уровень 2 внесите депозит от 500₽"
    },
    2: {
        "text": (
            "💰 <b>Уровень 2: 5 вращений (депозит от 500₽)</b>\n\n"
            "⚡ <i>Сейчас система раздает джекпоты!</i>\n\n"
            "Максимальный выигрыш: <b>15000₽</b>"
        ),
        "attempts": 5,
        "deposit": 500,
        "next_level_text": "Для Уровня 3 требуется депозит от 2000₽"
    },
    3: {
        "text": (
            "🚀 <b>Уровень 3: 10 вращений (депозит от 2000₽)</b>\n\n"
            "💎 <i>VIP-статус: +2 бонусных вращения!</i>\n\n"
            "Шанс на джекпот <b>увеличился в 3 раза</b>!"
        ),
        "attempts": 10,
        "deposit": 2000,
        "next_level_text": "Для Уровня 4 требуется депозит от 5000₽"
    },
    4: {
        "text": (
            "🤑 <b>Уровень 4: 15 вращений (депозит от 5000₽)</b>\n\n"
            "✨ <i>Эксклюзивно: гарантированный выигрыш!</i>\n\n"
            "Каждое 3-е вращение - <b>суперприз</b>!"
        ),
        "attempts": 15,
        "deposit": 5000,
        "next_level_text": "Финальный уровень: депозит от 15000₽"
    },
    5: {
        "text": (
            "🏆 <b>Уровень 5: 25 вращений (депозит от 15000₽)</b>\n\n"
            "💣 <i>Кристально чистая рулетка - без алгоритмов!</i>\n\n"
            "Последний шаг к <b>VIP-доступу</b>!"
        ),
        "attempts": 25,
        "deposit": 15000,
        "next_level_text": "Поздравляем с прохождением всех уровней!"
    }
}

# ================== КЛАВИАТУРЫ ================== #
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

def get_level_keyboard(level):
    web_app_url = "https://your-webapp.com/roulette"  # Замените на реальный URL
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
        [InlineKeyboardButton("🔄 Проверить депозит", callback_data=f"check_dep_{level}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_level_{level-1}" if level > 1 else "back_to_start")]
    ]

def get_vip_keyboard():
    return [
        [InlineKeyboardButton("💎 Забрать VIP-статус", url=PARTNER_LINK)],
        [InlineKeyboardButton("🎁 Забрать приз", url=VIP_BOT_LINK)],
        [InlineKeyboardButton("📢 Наш канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
    ]

# ================== ОБРАБОТЧИКИ ================== #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎰 <b>Добро пожаловать в VIP Казино!</b>\n\n"
        "🔹 Для доступа к рулетке:\n"
        "1. Зарегистрируйтесь по кнопке ниже (обязательно новый аккаунт!)\n"
        "2. Подтвердите регистрацию\n"
        "3. Получите 3 бесплатных вращения\n\n"
        "🔥 <i>Первые 50 игроков получают +1 бесплатное вращение!</i>",
        reply_markup=InlineKeyboardMarkup(get_start_keyboard()),
        parse_mode="HTML"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🛠 <b>Инструкция:</b>\n\n"
        "1. Регистрация через кнопку обязательна\n"
        "2. Используйте <b>новый аккаунт</b> (старые не подойдут)\n"
        "3. Если бот не видит регистрацию - подождите 5 минут\n\n"
        "Для связи с менеджером нажмите кнопку ниже:",
        reply_markup=InlineKeyboardMarkup(get_help_keyboard()),
        parse_mode="HTML"
    )

async def check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    registered = False
    
    async for msg in context.bot.get_chat_history(REG_CHANNEL, limit=100):
        if str(user_id) in msg.text:
            registered = True
            break
    
    if registered:
        await show_level(query, 1)
    else:
        await query.edit_message_text(
            "❌ <b>Регистрация не найдена!</b>\n\n"
            "Убедитесь, что вы:\n"
            "1. Создали <b>новый</b> аккаунт\n"
            "2. Перешли по ссылке из кнопки «🚀 Зарегистрироваться»\n\n"
            "Если ошибка повторяется — попробуйте снова:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Попробовать снова", url=PARTNER_LINK)],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]),
            parse_mode="HTML"
        )

async def check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    level = int(query.data.split('_')[2])
    user_id = query.from_user.id
    deposit_found = False
    
    async for msg in context.bot.get_chat_history(DEPOSIT_CHANNEL, limit=100):
        if str(user_id) in msg.text:
            deposit_amount = int(msg.text.split(':')[-1].strip())
            if deposit_amount >= LEVELS[level]['deposit']:
                deposit_found = True
                break
    
    if deposit_found:
        await show_level(query, level)
    else:
        await query.edit_message_text(
            f"⚠️ <b>Депозит от {LEVELS[level]['deposit']}₽ не найден!</b>\n\n"
            f"Для перехода на уровень {level} требуется:\n"
            f"1. Пополнение от {LEVELS[level]['deposit']}₽\n"
            f"2. Использование партнерской ссылки\n\n"
            "Попробуйте снова или обратитесь в поддержку:",
            reply_markup=InlineKeyboardMarkup(get_deposit_failed_keyboard(level)),
            parse_mode="HTML"
        )

async def show_level(query, level):
    await query.edit_message_text(
        LEVELS[level]["text"],
        reply_markup=InlineKeyboardMarkup(get_level_keyboard(level)),
        parse_mode="HTML"
    )

async def level_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current_level = int(query.data.split('_')[1])
    next_level = current_level + 1
    
    if next_level <= 5:
        await query.edit_message_text(
            f"🏅 <b>Уровень {current_level} пройден!</b>\n\n"
            f"{LEVELS[next_level]['next_level_text']}\n\n"
            "⏳ <i>Предложение доступно только 24 часа!</i>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    f"💳 Перейти на уровень {next_level}", 
                    callback_data=f"check_dep_{next_level}"
                )],
                [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
            ]),
            parse_mode="HTML"
        )
    else:
        await show_vip_message(query)

async def show_vip_message(query):
    await query.edit_message_text(
        "💎 <b>СЕНСАЦИЯ! ВЫ ВЫИГРАЛИ VIP-ДОСТУП!</b> 💎\n\n"
        "🔥 <i>Вы вошли в элитный 0.01% игроков!</i> 🔥\n\n"
        "С этого момента вам доступно:\n"
        "✅ Персональные сигналы от нашего бота\n"
        "✅ Эксклюзивные бонусы до 500%\n"
        "✅ Гарантированные выигрыши каждый день\n\n"
        "⏳ <i>Активируйте VIP-статус в течение 24 часов!</i>",
        reply_markup=InlineKeyboardMarkup(get_vip_keyboard()),
        parse_mode="HTML"
    )

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(query.message, context)

async def back_to_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level = int(query.data.split('_')[3])
    await show_level(query, level)

# ================== ЗАПУСК БОТА ================== #
def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    
    # Обработчики callback'ов
    app.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    app.add_handler(CallbackQueryHandler(check_deposit, pattern="^check_dep_"))
    app.add_handler(CallbackQueryHandler(level_complete, pattern="^complete_"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(back_to_level, pattern="^back_to_level_"))
    
    # Защита от конфликтов
    app.run_polling(
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
