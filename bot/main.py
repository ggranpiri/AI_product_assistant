from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from bot.handlers.help_command import send_help
from bot.handlers.recipe import recipe
from bot.handlers.start import start
from bot.handlers.shopping import shopping
from bot.handlers.buttons import button
from bot.handlers.favorites import send_favorites_menu
from bot.handlers.text_message import handle_text
from config import TOKEN

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("shopping", shopping))
    application.add_handler(CommandHandler("recipe", recipe))
    application.add_handler(CommandHandler("view_favorites", send_favorites_menu))
    application.add_handler(CommandHandler("help", send_help))

    application.run_polling()


if __name__ == "__main__":
    main()
