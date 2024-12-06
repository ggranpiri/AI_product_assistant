from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton
from telegram.ext import CallbackContext
from AI_product_assistant.bot.keyboards import favorites_menu_keyboard
from AI_product_assistant.bot.utils.bot_logging import log
from AI_product_assistant.bot.states import FAVORITES

USER_FAVORITES = {}  # {chat_id: [favorites_list]}

async def view_favorites(update: Update, context: CallbackContext) -> None:
    """Показывает список избранного."""
    chat_id = update.effective_chat.id
    log(update)

    favorites = USER_FAVORITES.get(chat_id, [])
    if favorites:
        favorites_text = "\n".join(f"- {item}" for item in favorites)
        await update.message.reply_text(
            f"Ваш список избранного:\n{favorites_text}",
            reply_markup=InlineKeyboardMarkup(favorites_menu_keyboard(chat_id))
        )
    else:
        await update.message.reply_text(
            "Ваш список избранного пока пуст.",
            reply_markup=InlineKeyboardMarkup(favorites_menu_keyboard(chat_id))
        )

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

