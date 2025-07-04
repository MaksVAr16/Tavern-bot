import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
import os

# Настройки
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
REG_CHANNEL = '-1002739343436'  # Канал с регистрациями
DEPOSIT_CHANNEL = '-1002690483167'  # Канал с депозитами
SUPPORT_LINK = 'https://t.me/Maksimmm16'  # Ссылка на поддержку
VIP_BOT_LINK = 'https://t.me/TESTVIPP_BOT'  # Ссылка на VIP-бота
CHANNEL_LINK = 'https://t.me/your_channel'  # Ссылка на канал (не указана, оставил заглушку)
PARTNER_LINK = 'https://tavern-bot.onrender.com'  # Партнерская ссылка
MINI_APP_LINK = 'https://t.me/Tavern_Rulet_bot/myapp'  # Ссылка на MiniApp

# Путь к папке с изображениями
IMAGE_FOLDER = r'C:\Users\Maks\Desktop\Traffic\BOT\telegram-casino-bot\rturtyk'

# Уровни пользователей
USER_LEVELS = {}

# Включим логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Пути к изображениям
IMAGE_PATHS = {
    'start': os.path.join(IMAGE_FOLDER, 'start.jpg'),
    'help': os.path.join(IMAGE_FOLDER, 'help.jpg'),
    'level1': os.path.join(IMAGE_FOLDER, 'level1.jpg'),
    'level2': os.path.join(IMAGE_FOLDER, 'level2.jpg'),
    'vip': os.path.join(IMAGE_FOLDER, 'vip.jpg')
}

# Функция для проверки регистрации/депозита
def check_user_in_channel(user_id: int, channel: str, context: CallbackContext) -> bool:
    try:
        messages = context.bot.get_chat_history(chat_id=channel, limit=100)
        for message in messages:
            if str(user_id) in message.text:
                return True
    except Exception as e:
        logger.error(f"Error checking channel: {e}")
    return False

# Обработчик команды /start
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    USER_LEVELS[user_id] = 0  # Устанавливаем начальный уровень
    
    keyboard = [
        [InlineKeyboardButton("🚀 Зарегистрироваться", url=PARTNER_LINK)],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data='check_reg')],
        [InlineKeyboardButton("❓ Нужна помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем изображение (если есть)
    photo = None
    if os.path.exists(IMAGE_PATHS['start']):
        photo = InputFile(IMAGE_PATHS['start'])
    
    if photo:
        update.message.reply_photo(
            photo=photo,
            caption="*🔥 Первые 50 игроков получают +1 бесплатное вращение\!*",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    else:
        update.message.reply_text(
            "*🔥 Первые 50 игроков получают +1 бесплатное вращение\!*",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

# Обработчик раздела помощи
def help_section(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📞 Менеджер", url=SUPPORT_LINK)],
        [InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем изображение (если есть)
    photo = None
    if os.path.exists(IMAGE_PATHS['help']):
        photo = InputFile(IMAGE_PATHS['help'])
    
    if photo:
        query.message.reply_photo(
            photo=photo,
            caption="*🛠 Используйте только новый аккаунт, иначе бот не увидит регистрацию\!*",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    else:
        query.message.reply_text(
            "*🛠 Используйте только новый аккаунт, иначе бот не увидит регистрацию\!*",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

# Проверка регистрации
def check_registration(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = update.effective_user.id
    query.answer()
    
    if check_user_in_channel(user_id, REG_CHANNEL, context):
        USER_LEVELS[user_id] = 1  # Переводим на уровень 1
        show_level(update, context, 1)
    else:
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", url=PARTNER_LINK)],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            text="*❌ Регистрация не найдена\! Попробуйте снова или обратитесь в поддержку\.*",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

# Проверка депозита
def check_deposit(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = update.effective_user.id
    query.answer()
    
    current_level = USER_LEVELS.get(user_id, 0)
    
    if check_user_in_channel(user_id, DEPOSIT_CHANNEL, context):
        USER_LEVELS[user_id] = current_level + 1  # Повышаем уровень
        show_level(update, context, current_level + 1)
    else:
        keyboard = [
            [InlineKeyboardButton("💳 Пополнить баланс", url=PARTNER_LINK)],
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f'check_deposit_{current_level}')],
            [InlineKeyboardButton("🔙 Назад", callback_data=f'level_{current_level}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            text=f"*⚠️ Депозит не найден\! Минимум {500 * current_level}₽ для Уровня {current_level + 1}\.*",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

# Показать уровень
def show_level(update: Update, context: CallbackContext, level: int) -> None:
    query = update.callback_query
    
    level_texts = {
        1: ("🎉 3 бесплатных вращения\! Выигрыши до 5000₽\!", "🎰 Крутить рулетку", "💎 VIP\-доступ"),
        2: ("💰 Уровень 2: 5 вращений \(депозит от 500₽\) \+ бонусы\!", "💳 Пополнить баланс", "🔄 Проверить депозит"),
        3: ("💰 Уровень 3: 7 вращений \(депозит от 1000₽\) \+ бонусы\!", "💳 Пополнить баланс", "🔄 Проверить депозит"),
        4: ("💰 Уровень 4: 10 вращений \(депозит от 2000₽\) \+ бонусы\!", "💳 Пополнить баланс", "🔄 Проверить депозит"),
        5: ("💰 Уровень 5: 15 вращений \(депозит от 5000₽\) \+ бонусы\!", "💳 Пополнить баланс", "🔄 Проверить депозит")
    }
    
    if level == 1:
        keyboard = [
            [InlineKeyboardButton(level_texts[1][1], url=MINI_APP_LINK)],
            [InlineKeyboardButton(level_texts[1][2], url=PARTNER_LINK)],
            [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
        ]
    elif level < 5:
        keyboard = [
            [InlineKeyboardButton(level_texts[level][1], url=PARTNER_LINK)],
            [InlineKeyboardButton(level_texts[level][2], callback_data=f'check_deposit_{level}')],
            [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
        ]
    else:  # VIP уровень
        show_vip(update, context)
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем изображение (если есть)
    photo = None
    image_key = f'level{level}' if level < 5 else 'vip'
    if os.path.exists(IMAGE_PATHS.get(image_key, '')):
        photo = InputFile(IMAGE_PATHS[image_key])
    
    if photo:
        query.message.reply_photo(
            photo=photo,
            caption=f"*{level_texts[level][0]}*",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    else:
        query.message.reply_text(
            f"*{level_texts[level][0]}*",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

# Показать VIP-доступ
def show_vip(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("💎 Получить VIP", url=PARTNER_LINK)],
        [InlineKeyboardButton("🎁 Забрать приз", url=VIP_BOT_LINK)],
        [InlineKeyboardButton("📢 Наш канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем изображение (если есть)
    photo = None
    if os.path.exists(IMAGE_PATHS['vip']):
        photo = InputFile(IMAGE_PATHS['vip'])
    
    if photo:
        query.message.reply_photo(
            photo=photo,
            caption="*💎 ВЫ ВЫИГРАЛИ VIP\-ДОСТУП\! Вы в топ\-0\.1% игроков\!*",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    else:
        query.message.reply_text(
            "*💎 ВЫ ВЫИГРАЛИ VIP\-ДОСТУП\! Вы в топ\-0\.1% игроков\!*",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

# Обработчик вращения рулетки
def spin(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    # Здесь должна быть логика рулетки, но это заглушка
    query.edit_message_text(
        text="*🎰 Вы получили 3 бесплатных вращения\! После вращений перейдите на следующий уровень\.*",
        parse_mode='MarkdownV2'
    )
    
    # Предлагаем перейти на уровень 2
    keyboard = [
        [InlineKeyboardButton("💎 VIP-доступ", url=PARTNER_LINK)],
        [InlineKeyboardButton("Перейти на Уровень 2", callback_data='level_2')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.message.reply_text(
        "*Хотите перейти на следующий уровень?*",
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )

# Назад в начало
def back_to_start(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    start(update, context)
    query.delete_message()

# Обработчик ошибок
def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update {update} caused error {context.error}')

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Обработчики команд
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(help_section, pattern='^help$'))
    dispatcher.add_handler(CallbackQueryHandler(check_registration, pattern='^check_reg$'))
    dispatcher.add_handler(CallbackQueryHandler(spin, pattern='^spin$'))
    dispatcher.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    dispatcher.add_handler(CallbackQueryHandler(show_vip, pattern='^vip$'))
    
    # Обработчики уровней
    dispatcher.add_handler(CallbackQueryHandler(show_level, pattern='^level_[1-5]$'))
    
    # Обработчики проверки депозита
    dispatcher.add_handler(CallbackQueryHandler(check_deposit, pattern='^check_deposit_[1-5]$'))
    
    # Обработчик ошибок
    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
