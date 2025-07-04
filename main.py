import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    filters
)
import os

# Настройки
TOKEN = '7888723857:AAHKmSMXxKFBiUpcgEDp0w_5Omh8SZhaW9I'
REG_CHANNEL = '@+-1002739343436'
DEPOSIT_CHANNEL = '@+-1002690483167'
SUPPORT_LINK = 'https://t.me/Maksimmm16'
VIP_BOT_LINK = 'https://t.me/TESTVIPP_BOT'
CHANNEL_LINK = 'https://t.me/your_channel'
PARTNER_LINK = 'https://tavern-bot.onrender.com'
MINI_APP_LINK = 'https://t.me/Tavern_Rulet_bot/myapp'

# Путь к изображениям
IMAGE_FOLDER = r'C:\Users\Maks\Desktop\Traffic\BOT\telegram-casino-bot\rturtyk'

# Уровни пользователей
USER_LEVELS = {}

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
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

# Тексты сообщений
TEXTS = {
    'start': "🔥 Первые 50 игроков получают +1 бесплатное вращение!",
    'help': "🛠 Используйте только новый аккаунт, иначе бот не увидит регистрацию!",
    'reg_not_found': "❌ Регистрация не найдена! Попробуйте снова или обратитесь в поддержку.",
    'deposit_not_found': "⚠️ Депозит не найден! Минимум {amount}₽ для Уровня {level}.",
    'spin_result': "🎰 Вы получили 3 бесплатных вращения! После вращений перейдите на следующий уровень.",
    'next_level': "Хотите перейти на следующий уровень?",
    'vip': "💎 ВЫ ВЫИГРАЛИ VIP-ДОСТУП! Вы в топ-0.1% игроков!",
    'levels': {
        1: ("🎉 3 бесплатных вращения! Выигрыши до 5000₽!", "🎰 Крутить рулетку", "💎 VIP-доступ"),
        2: ("💰 Уровень 2: 5 вращений (депозит от 500₽) + бонусы!", "💳 Пополнить баланс", "🔄 Проверить депозит"),
        3: ("💰 Уровень 3: 7 вращений (депозит от 1000₽) + бонусы!", "💳 Пополнить баланс", "🔄 Проверить депозит"),
        4: ("💰 Уровень 4: 10 вращений (депозит от 2000₽) + бонусы!", "💳 Пополнить баланс", "🔄 Проверить депозит"),
        5: ("💰 Уровень 5: 15 вращений (депозит от 5000₽) + бонусы!", "💳 Пополнить баланс", "🔄 Проверить депозит")
    }
}

def check_user_in_channel(user_id: int, channel: str, context: CallbackContext) -> bool:
    try:
        messages = context.bot.get_chat_history(chat_id=channel, limit=100)
        for message in messages:
            if str(user_id) in message.text:
                return True
    except Exception as e:
        logger.error(f"Error checking channel: {e}")
    return False

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    USER_LEVELS[user_id] = 0
    
    keyboard = [
        [InlineKeyboardButton("🚀 Зарегистрироваться", url=PARTNER_LINK)],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data='check_reg')],
        [InlineKeyboardButton("❓ Нужна помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    photo = None
    if os.path.exists(IMAGE_PATHS['start']):
        photo = InputFile(IMAGE_PATHS['start'])
    
    if photo:
        update.message.reply_photo(
            photo=photo,
            caption=TEXTS['start'],
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    else:
        update.message.reply_text(
            TEXTS['start'],
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

def help_section(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📞 Менеджер", url=SUPPORT_LINK)],
        [InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    photo = None
    if os.path.exists(IMAGE_PATHS['help']):
        photo = InputFile(IMAGE_PATHS['help'])
    
    if photo:
        query.message.reply_photo(
            photo=photo,
            caption=TEXTS['help'],
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    else:
        query.message.reply_text(
            TEXTS['help'],
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

def check_registration(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = update.effective_user.id
    query.answer()
    
    if check_user_in_channel(user_id, REG_CHANNEL, context):
        USER_LEVELS[user_id] = 1
        show_level(update, context, 1)
    else:
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", url=PARTNER_LINK)],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            text=TEXTS['reg_not_found'],
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

def check_deposit(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = update.effective_user.id
    query.answer()
    
    current_level = USER_LEVELS.get(user_id, 0)
    
    if check_user_in_channel(user_id, DEPOSIT_CHANNEL, context):
        USER_LEVELS[user_id] = current_level + 1
        show_level(update, context, current_level + 1)
    else:
        keyboard = [
            [InlineKeyboardButton("💳 Пополнить баланс", url=PARTNER_LINK)],
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f'check_deposit_{current_level}')],
            [InlineKeyboardButton("🔙 Назад", callback_data=f'level_{current_level}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            text=TEXTS['deposit_not_found'].format(amount=500*current_level, level=current_level+1),
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

def show_level(update: Update, context: CallbackContext, level: int) -> None:
    query = update.callback_query
    level_data = TEXTS['levels'].get(level)
    
    if level == 1:
        keyboard = [
            [InlineKeyboardButton(level_data[1], url=MINI_APP_LINK)],
            [InlineKeyboardButton(level_data[2], url=PARTNER_LINK)],
            [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
        ]
    elif level < 5:
        keyboard = [
            [InlineKeyboardButton(level_data[1], url=PARTNER_LINK)],
            [InlineKeyboardButton(level_data[2], callback_data=f'check_deposit_{level}')],
            [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
        ]
    else:
        show_vip(update, context)
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    photo = None
    image_key = f'level{level}' if level < 5 else 'vip'
    if os.path.exists(IMAGE_PATHS.get(image_key, '')):
        photo = InputFile(IMAGE_PATHS[image_key])
    
    if photo:
        query.message.reply_photo(
            photo=photo,
            caption=level_data[0],
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    else:
        query.message.reply_text(
            level_data[0],
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

def show_vip(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("💎 Получить VIP", url=PARTNER_LINK)],
        [InlineKeyboardButton("🎁 Забрать приз", url=VIP_BOT_LINK)],
        [InlineKeyboardButton("📢 Наш канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton("❓ Помощь", url=SUPPORT_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    photo = None
    if os.path.exists(IMAGE_PATHS['vip']):
        photo = InputFile(IMAGE_PATHS['vip'])
    
    if photo:
        query.message.reply_photo(
            photo=photo,
            caption=TEXTS['vip'],
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    else:
        query.message.reply_text(
            TEXTS['vip'],
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

def spin(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        text=TEXTS['spin_result'],
        parse_mode='MarkdownV2'
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 VIP-доступ", url=PARTNER_LINK)],
        [InlineKeyboardButton("Перейти на Уровень 2", callback_data='level_2')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.message.reply_text(
        TEXTS['next_level'],
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )

def back_to_start(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    start(update, context)
    query.delete_message()

def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update {update} caused error {context.error}')

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(help_section, pattern='^help$'))
    dispatcher.add_handler(CallbackQueryHandler(check_registration, pattern='^check_reg$'))
    dispatcher.add_handler(CallbackQueryHandler(spin, pattern='^spin$'))
    dispatcher.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    dispatcher.add_handler(CallbackQueryHandler(show_vip, pattern='^vip$'))
    dispatcher.add_handler(CallbackQueryHandler(show_level, pattern='^level_[1-5]$'))
    dispatcher.add_handler(CallbackQueryHandler(check_deposit, pattern='^check_deposit_[1-5]$'))
    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
