import os
import logging
import asyncio
import httpx
import psycopg
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from flask import Flask, request
from dotenv import load_dotenv

# Усиленная настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Загрузка переменных окружения
load_dotenv()

# Конфиг
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_PARTNER_URL = "https://1wilib.life/?open=register&p=2z3v"
SUPPORT_LINK = "https://t.me/Maksimmm16"
MINI_APP_URL = "https://t.me/Tavern_Rulet_bot/ere"
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)

# Генератор партнерской ссылки с user_id
def generate_partner_url(user_id: str) -> str:
    url = f"{BASE_PARTNER_URL}&ref={user_id}"
    logger.debug(f"🔗 Сгенерирована партнерская ссылка для user_id={user_id}: {url}")
    return url

# Инициализация базы данных
def init_db():
    try:
        logger.info("🔄 Попытка инициализации БД...")
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS registered_users (
                        user_id TEXT PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info("✅ База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка инициализации БД: {e}", exc_info=True)

def save_user_id(user_id: str):
    try:
        logger.debug(f"🔄 Попытка сохранения user_id={user_id} в БД")
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO registered_users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
                    (user_id,)
                )
                conn.commit()
                logger.info(f"✅ Юзер {user_id} успешно сохранён в БД")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения пользователя {user_id}: {e}", exc_info=True)

def is_user_registered(user_id: str) -> bool:
    try:
        logger.debug(f"🔄 Проверка регистрации для user_id={user_id}")
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM registered_users WHERE user_id = %s",
                    (user_id,)
                )
                result = cursor.fetchone() is not None
                logger.info(f"🔍 Результат проверки регистрации: user_id={user_id}, зарегистрирован={result}")
                return result
    except Exception as e:
        logger.error(f"❌ Ошибка проверки регистрации для user_id={user_id}: {e}", exc_info=True)
        return False

# Инициализация БД при старте
logger.info("🔄 Запуск инициализации БД...")
init_db()

# Вебхук для регистрации
@app.route('/1win_webhook', methods=['GET'])
def handle_webhook():
    try:
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        logger.info(f"🔄 Получен вебхук: user_id={user_id}, status={status}")
        
        if not user_id or not status:
            logger.warning(f"⚠️ Неполные данные в вебхуке: user_id={user_id}, status={status}")
            return "Missing parameters", 400
            
        if status == "success":
            logger.debug(f"🔄 Обработка успешной регистрации user_id={user_id}")
            save_user_id(user_id)
            logger.info(f"✅ Успешно обработан вебхук для user_id={user_id}")
            return "OK", 200
        else:
            logger.warning(f"⚠️ Неуспешный статус в вебхуке: user_id={user_id}, status={status}")
            return "Invalid status", 400
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в обработке вебхука: {e}", exc_info=True)
        return "Server Error", 500

# ===== DEBUG FUNCTIONS START =====
@app.route('/debug_db')
def debug_db():
    """Отладочная страница для проверки базы данных"""
    try:
        result = []
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                # Проверка подключения
                cursor.execute("SELECT 1")
                result.append("✅ Подключение к Neon: работает")
                
                # Проверка количества записей
                cursor.execute("SELECT COUNT(*) FROM registered_users")
                count = cursor.fetchone()[0]
                result.append(f"📊 Всего записей: {count}")
                
                # Последние 5 записей
                cursor.execute("SELECT user_id, timestamp FROM registered_users ORDER BY timestamp DESC LIMIT 5")
                result.append("\nПоследние 5 записей:")
                for row in cursor.fetchall():
                    result.append(f"👤 {row[0]} - {row[1]}")
        
        return "<pre>" + "\n".join(result) + "</pre>"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

async def debug_command(update: Update, context):
    """Команда /debug для проверки базы"""
    try:
        # Получаем статистику
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM registered_users")
                count = cursor.fetchone()[0]
        
        await update.message.reply_text(
            f"🛠️ <b>Отладочная информация</b>\n\n"
            f"• Подключение к Neon: <b>работает</b>\n"
            f"• Записей в базе: <b>{count}</b>\n\n"
            f"Полный отчёт: https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/debug_db",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
# ===== DEBUG FUNCTIONS END =====

# Команда /start
async def start(update: Update, context):
    user_id = str(update.effective_user.id)
    logger.debug(f"🔄 Обработка команды /start для user_id={user_id}")
    
    try:
        partner_url = generate_partner_url(user_id)
        keyboard = [
            [InlineKeyboardButton("🔹 Зарегистрироваться", url=partner_url)],
            [
                InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg"),
                InlineKeyboardButton("❓ Нужна помощь", callback_data="help")
            ]
        ]
        
        message_text = (
            "🎰 <b>Ты уже на полпути к победе...</b>\n\n"
            "1. Нажми «Зарегистрироваться»\n"
            "2. Создай <b>НОВЫЙ аккаунт</b>\n"
            "3. Нажми «Я зарегистрировался»"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        logger.info(f"✅ Успешно обработан /start для user_id={user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка в обработке /start для user_id={user_id}: {e}", exc_info=True)

# Проверка регистрации
async def check_registration(update: Update, context):
    user_id = str(update.effective_user.id)
    logger.debug(f"🔄 Проверка регистрации для user_id={user_id}")
    
    try:
        registered = is_user_registered(user_id)
        logger.debug(f"🔍 Результат проверки для user_id={user_id}: {registered}")
        
        if registered:
            keyboard = [
                [InlineKeyboardButton("🎰 Перейти к рулетке", url=MINI_APP_URL)],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            text = "🎉 <b>Регистрация подтверждена!</b>"
            logger.info(f"✅ Подтверждена регистрация user_id={user_id}")
        else:
            partner_url = generate_partner_url(user_id)
            keyboard = [
                [InlineKeyboardButton("🔹 Попробовать ещё раз", url=partner_url)],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            text = "❌ <b>Регистрация не найдена!</b>"
            logger.warning(f"⚠️ Регистрация не найдена для user_id={user_id}")
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка проверки регистрации для user_id={user_id}: {e}", exc_info=True)
        await update.callback_query.edit_message_text("⚠️ Ошибка сервера")

# Кнопка помощи
async def help_button(update: Update, context):
    user_id = str(update.effective_user.id)
    logger.debug(f"🔄 Обработка кнопки помощи для user_id={user_id}")
    
    try:
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")],
            [InlineKeyboardButton("📞 Менеджер", url=SUPPORT_LINK)]
        ]
        await update.callback_query.edit_message_text(
            "🛠 <b>Центр помощи</b>\n\n"
            "Для связи с менеджером:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        logger.info(f"✅ Успешно обработана кнопка помощи для user_id={user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка обработки кнопки помощи для user_id={user_id}: {e}", exc_info=True)

# Назад в начало
async def back_to_start(update: Update, context):
    user_id = str(update.effective_user.id)
    logger.debug(f"🔄 Обработка возврата в начало для user_id={user_id}")
    
    try:
        partner_url = generate_partner_url(user_id)
        keyboard = [
            [InlineKeyboardButton("🔹 Зарегистрироваться", url=partner_url)],
            [
                InlineKeyboardButton("✅ Я зарегистрировался", callback_data="check_reg"),
                InlineKeyboardButton("❓ Нужна помощь", callback_data="help")
            ]
        ]
        await update.callback_query.edit_message_text(
            "🎰 <b>Ты уже на полпути к победе...</b>\n\n"
            "1. Нажми «Зарегистрироваться»\n"
            "2. Создай <b>НОВЫЙ аккаунт</b>\n"
            "3. Нажми «Я зарегистрировался»",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка обработки возврата для user_id={user_id}: {e}", exc_info=True)

# Запуск Flask
def run_flask():
    try:
        port = 10000  # Жестко заданный порт
        logger.info(f"🔄 Запуск Flask сервера на порту {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"❌ Ошибка Flask: {e}", exc_info=True)
        raise

async def close_previous_connections():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/close",
                timeout=10
            )
            if response.status_code == 200:
                logger.info("✅ Успешно закрыты предыдущие соединения бота")
            else:
                logger.warning(f"⚠️ Не удалось закрыть соединения: {response.text}")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при закрытии соединений: {e}")

# Основная функция для запуска бота
async def main():
    try:
        # Проверка обязательных переменных
        if not BOT_TOKEN:
            raise ValueError("❌ Не задан BOT_TOKEN")
        if not DATABASE_URL:
            raise ValueError("❌ Не задан DATABASE_URL")
            
        await close_previous_connections()
        
        logger.info("🔄 Инициализация бота...")
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("debug", debug_command))  # Добавлена новая команда
        bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
        bot_app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
        bot_app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
        
        # Запускаем Flask в отдельном потоке
        logger.info("🔄 Запуск Flask в отдельном потоке...")
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        # Запускаем бота
        logger.info("🔄 Запуск бота...")
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
        
        logger.info("✅ Бот успешно запущен и готов к работе!")
        
        # Бесконечный цикл
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Фатальная ошибка: {e}", exc_info=True)
