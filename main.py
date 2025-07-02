import os
import logging
import asyncio
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from flask import Flask, request
from datetime import datetime

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
ADMIN_ID = "8037553363"  # Твой ID для отладки

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
        deposit = request.args.get('deposit', '0')
        
        logger.info(f"Получен вебхук: user_id={user_id}, status={status}, deposit={deposit}")
        
        if status == "success" and user_id and int(deposit) >= 100:
            with open(REGISTERED_USERS_FILE, 'a') as f:
                f.write(f"{user_id}\n")
            logger.info(f"Успешная регистрация: {user_id}")
            return "OK", 200
            
        return "Error: Need deposit 100+ RUB", 400
        
    except Exception as e:
        logger.error(f"Ошибка вебхука: {str(e)}")
        return "Server Error", 500

async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
        [
            InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg"),
            InlineKeyboardButton("🆘 Помощь", callback_data="help")
        ]
    ]
    text = (
        "🎉 <b>Добро пожаловать в букмекер-бота!</b>\n\n"
        "💰 <b>Для получения бонуса:</b>\n"
        "1. Нажми «Зарегистрироваться»\n"
        "2. Создай <b>НОВЫЙ аккаунт</b>\n"
        "3. Пополни баланс <b>от 100₽</b>\n"
        "4. Нажми «Я зарегистрировался»\n\n"
        "⚠️ <i>Без депозита бонус не начисляется!</i>"
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
            await update.callback_query.edit_message_text(
                "✅ <b>Регистрация и депозит подтверждены!</b>\n\n"
                "Ваш бонус будет начислен в течение 24 часов.",
                parse_mode="HTML"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔹 Зарегистрироваться", url=PARTNER_URL)],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            await update.callback_query.edit_message_text(
                "❌ <b>Аккаунт не найден или депозит менее 100₽</b>\n\n"
                "1. Зарегистрируйтесь по ссылке выше\n"
                "2. Пополните баланс от 100₽\n"
                "3. Попробуйте снова",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка проверки: {str(e)}")
        await update.callback_query.edit_message_text("⚠️ Ошибка сервера. Попробуйте позже.")

async def manual_check(update: Update, context):
    user_id = str(update.effective_user.id)
    
    try:
        # Проверяем, есть ли уже такой ID
        with open(REGISTERED_USERS_FILE, 'r+') as f:
            existing_ids = f.read()
            if user_id in existing_ids:
                await update.message.reply_text("⚠️ Ваш ID уже был добавлен ранее!")
                return
            
            # Добавляем ID
            f.write(f"{user_id}\n")
        
        await update.message.reply_text(
            "✅ <b>Ваш ID успешно добавлен вручную!</b>\n\n"
            "Если бонус не пришел в течение 24 часов:\n"
            "1. Проверьте пополнение счета\n"
            "2. Напишите поддержку 1Win\n"
            "3. Свяжитесь с нами: @Maksimmm16",
            parse_mode="HTML"
        )
        
        # Уведомление админу
        if str(update.effective_user.id) != ADMIN_ID:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ Ручная проверка: {user_id}"
            )
            
    except Exception as e:
        logger.error(f"Ошибка ручной проверки: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка сервера. Попробуйте позже.")

async def help_button(update: Update, context):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")],
        [InlineKeyboardButton("📞 Написать оператору", url=SUPPORT_LINK)]
    ]
    await update.callback_query.edit_message_text(
        "🛠 <b>Центр помощи</b>\n\n"
        "Если у вас проблемы:\n"
        "1. Обязательно создавайте <b>новый аккаунт</b>\n"
        "2. Пополняйте баланс <b>от 100₽</b>\n"
        "3. Напишите любое сообщение в чат для ручной проверки\n\n"
        "<i>Без депозита бонус не начисляется!</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def back_to_start(update: Update, context):
    await start(update, context)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

async def run_bot():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manual_check))
    
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
