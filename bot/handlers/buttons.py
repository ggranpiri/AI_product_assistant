from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from bot.states.user_states import USER_STATE, FAVORITES, PREV_MESSAGE
from bot.handlers.favorites import send_favorites_menu

async def send_main_menu(update: Update, context: CallbackContext, text: str) -> None:
    """Отправка главного меню с кастомным текстом."""
    chat_id = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("🍎 Составить корзину", callback_data='shopping')]
    ]

    if chat_id in FAVORITES and FAVORITES[chat_id]:
        keyboard.append([InlineKeyboardButton("Просмотреть избранное", callback_data='view_favorites')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)



async def button(update: Update, context: CallbackContext) -> None:
    """Обработка нажатий кнопок."""
    query = update.callback_query
    chat_id = query.message.chat.id
    await query.answer()

    if query.data == 'shopping':
        USER_STATE[chat_id] = 'shopping'
        await query.edit_message_text("Опишите, что хотите приготовить или введите список продуктов.")
    elif query.data == 'add_to_favorites':
        USER_STATE[chat_id] = 'naming_cart'
        await query.edit_message_text("Как вы хотите назвать свою корзину?")
    elif query.data.startswith('view_cart:'):
        cart_name = query.data.split(':', 1)[1]
        favorite_cart = FAVORITES.get(chat_id, {}).get(cart_name, [])
        total_price = sum(item.get('price', 0) for item in favorite_cart)
        formatted_cart = PREV_MESSAGE[chat_id]

        keyboard = [
            [InlineKeyboardButton("Удалить корзину", callback_data=f"delete_cart:{cart_name}")],
            [InlineKeyboardButton("Назад", callback_data='view_favorites')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"Содержимое корзины '{cart_name}':\n\n{formatted_cart}\n\nИтоговая стоимость: {total_price} ₽",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    elif query.data.startswith('delete_cart:'):
        cart_name = query.data.split(':', 1)[1]
        if chat_id in FAVORITES and cart_name in FAVORITES[chat_id]:
            del FAVORITES[chat_id][cart_name]
        await send_favorites_menu(update, context)
    elif query.data == 'choose_another_name':
        USER_STATE[chat_id] = 'naming_cart'
        await query.edit_message_text("Введите новое имя для корзины.")
    elif query.data == 'cancel_addition':
        USER_STATE.pop(chat_id, None)
        await send_main_menu(update, context, "Могу ли я вам ещё чем-нибудь помочь?")
    elif query.data == 'back':
        await send_main_menu(update, context, "Могу ли я вам ещё чем-нибудь помочь?")
    elif query.data == 'view_favorites':
        await send_favorites_menu(update, context)

