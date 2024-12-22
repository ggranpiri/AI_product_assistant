from telegram import Update
from telegram.ext import CallbackContext
from bot.handlers.handle_naming_cart import process_naming_cart
from bot.handlers.handle_recipe import process_recipe

from bot.handlers.handle_shopping import process_shopping
from bot.utils.logger import log
from bot.states.user_states import USER_STATE


async def handle_text(update: Update, context: CallbackContext) -> None:
    """Обработка текстовых сообщений."""
    log(update)
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    state = USER_STATE.get(chat_id)

    if state == 'shopping':
        await process_shopping(update, context, chat_id, text)

    elif state == 'naming_cart':
        await process_naming_cart(update, context, chat_id, text)

    elif state == 'recipe':
        await process_recipe(update, context, text, chat_id)

    else:
        await update.message.reply_text("Пожалуйста, выберите команду из меню.")

