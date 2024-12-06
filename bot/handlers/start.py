from telegram import InlineKeyboardMarkup, Update
from AI_product_assistant.bot.keyboards import main_menu_keyboard
from AI_product_assistant.bot.states import USER_STATE
from AI_product_assistant.bot.handlers.favorites import send_favorites_menu
from telegram.ext import CallbackContext


async def start_command(update: Update, context: CallbackContext) -> None:
    """Стартовое сообщение и основное меню."""
    await send_main_menu(update, context, "Я — ваш умный помощник, который поможет:\n"
                                          "- 🛒 Составить удобный список покупок.\n"
                                          "- 🥗 Создать вкусный рецепт из ваших продуктов.\n\n")


async def send_main_menu(update: Update, context: CallbackContext, text: str) -> None:
    """Отправка главного меню с кастомным текстом."""
    chat_id = update.effective_chat.id
    reply_markup = InlineKeyboardMarkup(main_menu_keyboard(chat_id))

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def button_handler(update: Update, context: CallbackContext) -> None:
    """Обработка нажатий кнопок."""
    query = update.callback_query
    chat_id = query.message.chat.id
    await query.answer()

    if query.data == 'shopping':
        USER_STATE[chat_id] = 'shopping'
        await query.edit_message_text("Опишите, что хотите приготовить или введите список продуктов.")
    elif query.data == 'view_favorites':
        await send_favorites_menu(update, context)
    else:
        await send_main_menu(update, context, "Могу ли я вам ещё чем-нибудь помочь?")
