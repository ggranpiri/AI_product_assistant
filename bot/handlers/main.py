from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from AI_product_assistant.bot.handlers import start, shopping, favorites
from AI_product_assistant.parser.update_bd import auto_update_bd
import threading
from AI_product_assistant import config

def main() -> None:
    """Основной запуск бота."""
    application = Application.builder().token(config.TOKEN).build()

    # Регистрация хендлеров
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, shopping.handle_text))
    application.add_handler(CallbackQueryHandler(start.button_handler))
    application.add_handler(CommandHandler("shopping", shopping.shopping_command))
    application.add_handler(CommandHandler("view_favorites", favorites.view_favorites))

    # Запуск бота
    application.run_polling()

    # Запуск автообновления базы данных
    update_thread = threading.Thread(target=auto_update_bd)
    update_thread.start()


if __name__ == "__main__":
    main()
