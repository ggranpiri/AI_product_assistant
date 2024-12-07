from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from AI_product_assistant.bot.states.user_states import FAVORITES

async def send_favorites_menu(update: Update, context: CallbackContext) -> None:
    """Отправка меню с избранными корзинами."""
    chat_id = update.effective_chat.id
    favorite_carts = FAVORITES.get(chat_id, {})

    if not favorite_carts:
        if update.callback_query:
            await update.callback_query.edit_message_text("У вас пока нет избранных корзин.")
        elif update.message:
            await update.message.reply_text("У вас пока нет избранных корзин.")
        return

    keyboard = [[InlineKeyboardButton(cart_name, callback_data=f"view_cart:{cart_name}")]
                for cart_name in favorite_carts]
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text("Ваши избранные корзины:", reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text("Ваши избранные корзины:", reply_markup=reply_markup)

