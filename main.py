# В начало файла добавить
import atexit

# Изменённая функция вебхука
@app.route('/1win_webhook', methods=['GET', 'POST'])
def handle_1win_webhook():
    try:
        # Формируем абсолютный путь к файлу
        file_path = os.path.abspath(REGISTERED_USERS_FILE)
        
        # Логируем путь для отладки
        logger.info(f"Путь к файлу: {file_path}")
        
        # Получаем данные
        user_id = request.args.get('user_id') or (request.json and request.json.get('user_id'))
        status = request.args.get('status') or (request.json and request.json.get('status'))
        
        if not user_id:
            return "user_id required", 400
        
        logger.info(f"Получен запрос: user_id={user_id}, status={status}")
        
        # Гарантируем существование файла
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                logger.info(f"Создан новый файл: {file_path}")
        
        if status == "success":
            with open(file_path, 'a+') as f:
                f.seek(0)
                if str(user_id) not in f.read():
                    f.write(f"{user_id}\n")
                    logger.info(f"Успешная регистрация: {user_id}")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Ошибка в вебхуке: {str(e)}", exc_info=True)
        return "Server Error", 500

# Изменённый запуск бота
def run_bot():
    # Создаём файл при старте
    file_path = os.path.abspath(REGISTERED_USERS_FILE)
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            logger.info(f"Создан файл при старте: {file_path}")
    
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    # Ваши обработчики
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_registration, pattern="^check_reg$"))
    bot_app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    return bot_app

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Настраиваем бота
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        bot = run_bot()
        loop.run_until_complete(bot.initialize())
        loop.run_until_complete(bot.start())
        loop.run_until_complete(bot.updater.start_polling(drop_pending_updates=True))
        logger.info("Бот успешно запущен")
        loop.run_forever()
    except Exception as e:
        logger.error(f"Ошибка запуска: {str(e)}")
    finally:
        loop.close()
