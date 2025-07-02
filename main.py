import os
import logging
import asyncio
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from flask import Flask, request

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфиг
BOT_TOKEN = os.getenv("BOT_TOKEN")
PARTNER_URL = "https://1wilib.life/?open=register&p=2z3v"
SUPPORT_LINK = "https://t.me/Maksimmm16"
REGISTERED_USERS_FILE = os.path.abspath("registered_users.txt")
MINI_APP_URL = "https://t.me/Tavern_Rulet_bot/ere"  # Замени на реальный URL когда будет готово

# Создаем файл если его нет
if not os.path.exists(REGISTERED_USERS_FILE):
    with open(REGISTERED_USERS_FILE, 'w') as f:
        logger.info(f"Создан файл: {REGISTERED_USERS_FILE}")

app = Flask(__name__)

@app.route('/1win_webhook', methods=['GET'])
def handle_webhook():
    try:
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        
        logger.info(f"Получен вебхук: user_id={user_id}, status={status}")
        
        if status == "success" and user_id:
            with open(REGISTERED_USERS_FILE, 'a') as f:
                f.write(f"{user_id}\n")
            logger.info(f"Успешная регистрация: {user_id}")
            return "OK", 200
            
        return "Error: Invalid data", 400
        
    except Exception as e:
        logger.error(f"Ошибка вебхука: {str(e)}")
        return "Server Error", 500

async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
        [
            InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg"),
            InlineKeyboardButton("❓ Нужна помощь", callback_data="help")
        ]
    ]
    text = (
        "🎰 <b>Ты уже на полпути к победе...</b>\n\n"
        "1. Нажми «Зарегистрироваться»\n"
        "2. Создай <b>НОВЫЙ аккаунт</b> (вход в старый не подойдёт!)\n"
        "3. Вернись и нажми «Я зарегистрировался»"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def check_registration(update: Update, context):
    user_id = str(update.effective_user.id)
    
    try:
        with open(REGISTERED_USERS_FILE, 'r') as f:
            registered = user_id in f.read()
            
        if registered:
            keyboard = [
                [InlineKeyboardButton("🎰 Перейти к рулетке", url=MINI_APP_URL)],
                [InlineKeyboardButton("❓ Нужна помощь", callback_data="help")]
            ]
            await update.callback_query.edit_message_text(
                "🎉 <b>Поздравляем! Ты почти у цели...</b>\n\n"
                "Теперь тебе доступна рулетка с бонусами:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔹 Попробовать ещё раз", url=PARTNER_URL)],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            await update.callback_query.edit_message_text(
                "❌ <b>Регистрация не найдена!</b>\n\n"
                "👉 Попробуйте ещё раз. Зарегистрируйте <b>НОВЫЙ аккаунт</b> по ссылке выше.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка проверки: {str(e)}")
        await update.callback_query.edit_message_text("⚠️ Ошибка сервера. Попробуйте позже.")

async def help_button(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")],
        [InlineKeyboardButton("📞 Связаться с менеджером", url=SUPPORT_LINK)]
    ]
    await update.callback_query.edit_message_text(
        "🛠 <b>Центр помощи</b>\n\n"
        "Если возникли проблемы:\n"
        "• Обязательно создавайте <b>НОВЫЙ аккаунт</b>\n"
        "• Для срочной помощи напишите менеджеру:\n\n"
        f"👉 <a href='{SUPPORT_LINK}'>Максим (нажмите здесь)</a>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def back_to_start(update: Update, context):
    await start(update, context)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

async def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики (ВАЖНО: ручной ввод УДАЛЕН, остальное без изменений)
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    logger.info("Бот запущен")
    return bot_app

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        bot = loop.run_until_complete(run_bot())
        loop.run_forever()
    except Exception as e:
        logger.error(f"Ошибка запуска: {str(e)}")
    finally:
        loop.close()
