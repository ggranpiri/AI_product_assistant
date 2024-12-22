from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from bot.handlers.handle_format import format_ingredients_list
from bot.handlers.handle_recipe import fetch_ingredients_list
from bot.states.user_states import PURCHASE_HISTORY, PREV_MESSAGE, USER_STATE
from parser.match_product import get_links_from_list
from config import BD_path


async def process_shopping(update: Update, context: CallbackContext, chat_id: int, text: str) -> None:
    """Обработка состояния 'shopping'."""
    processing_message = await update.message.reply_text("Ваш запрос обрабатывается, пожалуйста, подождите...")

    ingredients_list = fetch_ingredients_list(text)
    if not ingredients_list:
        await processing_message.edit_text(
            "Извините, нам не удалось найти подходящие продукты. Пожалуйста, повторите ваш запрос еще раз.")
        return

    ingredients_list_with_links = get_links_from_list(ingredients_list, BD_path)
    context.user_data["last_cart"] = ingredients_list_with_links

    if not ingredients_list_with_links:
        await processing_message.edit_text(
            "Извините, нам не удалось вам помочь. Пожалуйста, повторите ваш запрос еще раз.")
        return

    total_price, formatted_list = format_ingredients_list(ingredients_list, ingredients_list_with_links)

    await processing_message.edit_text(
        f"Ваш список продуктов готов:\n{formatted_list}\n\nИтоговая стоимость: {total_price} ₽",
        parse_mode="Markdown"
    )

    keyboard = [
        [InlineKeyboardButton("Да", callback_data='add_to_favorites')],
        [InlineKeyboardButton("Нет", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Хотите ли вы добавить эту корзину в избранное?", reply_markup=reply_markup)

    PURCHASE_HISTORY.setdefault(chat_id, []).append(ingredients_list_with_links)
    USER_STATE[chat_id] = 'ask_favorite'
    PREV_MESSAGE[chat_id] = formatted_list
