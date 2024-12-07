from telegram import Update
from telegram.ext import CallbackContext
from AI_product_assistant.bot.utils.logger import log
from AI_product_assistant.bot.handlers.buttons import send_main_menu

async def start(update: Update, context: CallbackContext) -> None:
    log(update)
    await send_main_menu(update, context, "Я — ваш умный помощник, который поможет:\n"
                                          "- 🛒 Составить удобный список покупок.\n"
                                          "- 🥗 Создать вкусный рецепт из ваших продуктов.\n\n")
