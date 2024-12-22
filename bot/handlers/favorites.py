from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from bot.states.user_states import FAVORITES

async def send_favorites_menu(update: Update, context: CallbackContext) -> None:
    """Отправка меню с избранными корзинами."""
    chat_id = update.effective_chat.id
    favorite_carts = FAVORITES.get(chat_id, {})

    if not favorite_carts:
        # Если корзин нет, отправляем сообщение и оставляем его на экране
        if update.callback_query:
            await update.callback_query.edit_message_text("У вас больше нет избранных корзин.")
        elif update.message:
            await update.message.reply_text("У вас больше нет избранных корзин.")

        # Создаем клавиатуру с двумя кнопками
        keyboard = [
            [InlineKeyboardButton("Составить корзину", callback_data='create_cart')],
            [InlineKeyboardButton("Составить рецепт", callback_data='recipe')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем предложение помощи с кнопками, но проверяем, откуда пришел запрос
        if update.callback_query:
            # Для callback_query используем answer_callback_query
            await update.callback_query.answer()  # Закрытие callback_query
            await update.callback_query.edit_message_text("Чем я могу вам еще помочь?", reply_markup=reply_markup)
        elif update.message:
            # Если это обычное сообщение, отправляем новое сообщение
            await update.message.reply_text("Чем я могу вам еще помочь?", reply_markup=reply_markup)

        return

    # Если корзины есть, показываем их
    keyboard = [[InlineKeyboardButton(cart_name, callback_data=f"view_cart:{cart_name}")]
                for cart_name in favorite_carts]
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text("Ваши избранные корзины:", reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text("Ваши избранные корзины:", reply_markup=reply_markup)
