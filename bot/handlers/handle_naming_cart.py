from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackContext

from bot.handlers.buttons import send_main_menu
from bot.states.user_states import USER_STATE, FAVORITES


async def process_naming_cart(update: Update, context: CallbackContext, chat_id: int, text: str) -> None:
    """Обработка состояния 'naming_cart'."""
    if not text:
        await update.message.reply_text("Пожалуйста, введите корректное название корзины.")
        return

    if chat_id in FAVORITES and text in FAVORITES[chat_id]:
        keyboard = [
            [InlineKeyboardButton("Выбрать другое имя", callback_data='choose_another_name')],
            [InlineKeyboardButton("Отмена добавления", callback_data='cancel_addition')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Корзина с именем '{text}' уже существует. Выберите одно из действий:",
            reply_markup=reply_markup
        )
        USER_STATE[chat_id] = 'naming_conflict'
        return

    last_cart = context.user_data.get("last_cart")
    if not last_cart:
        await update.message.reply_text("Ошибка: нет последней корзины для сохранения.")
        return

    FAVORITES.setdefault(chat_id, {})[text] = last_cart
    await update.message.reply_text(f"Корзина '{text}' добавлена в избранное!")

    USER_STATE.pop(chat_id, None)
    await send_main_menu(update, context, "Могу ли я вам ещё чем-нибудь помочь?")