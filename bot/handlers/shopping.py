from telegram import Update
from telegram.ext import CallbackContext
from AI_product_assistant.bot.utils.logger import log
from AI_product_assistant.bot.states.user_states import USER_STATE


async def shopping(update: Update, context: CallbackContext) -> None:
    log(update)
    chat_id = update.effective_chat.id
    USER_STATE[chat_id] = 'shopping'
    await update.message.reply_text("Вы выбрали: Составить корзину. Опишите, что хотите приготовить или введите список продуктов.")
