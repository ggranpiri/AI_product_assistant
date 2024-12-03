import asyncio
from datetime import datetime
from lib2to3.fixes.fix_input import context

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters
import config
from gpt_request import get_ingredients_list
from parser import get_links_from_list
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)

USER_STATE = {}
FAVORITES = {}
PURCHASE_HISTORY = {}


def get_date() -> str:
    """Получение текущей даты и времени в формате строки."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(update: Update) -> None:
    """Логирование действий пользователя."""
    if update.message:
        user = update.message.from_user
        name = f"{user.first_name} {user.last_name or ''}".strip()
        text = update.message.text
        print(f'{get_date()} - {name} (id {user.id}) написал: "{text}"')
    elif update.callback_query:
        query = update.callback_query
        user = query.from_user
        action = query.data
        print(f'{get_date()} - {user.first_name} (id {user.id}) нажал кнопку: "{action}"')
    else:
        print(f"{get_date()} - system_log: Неизвестное действие")


async def start(update: Update, context: CallbackContext) -> None:
    """Стартовое сообщение и основное меню."""
    await send_main_menu(update, context, "Я — ваш умный помощник, который поможет:\n"
                                          "- 🛒 Составить удобный список покупок.\n"
                                          "- 🥗 Создать вкусный рецепт из ваших продуктов.\n\n")


async def send_main_menu(update: Update, context: CallbackContext, text: str) -> None:
    """Отправка главного меню с кастомным текстом."""
    keyboard = [
        [InlineKeyboardButton("🍎 Составить корзину", callback_data='shopping')],
        [InlineKeyboardButton("Просмотреть избранное", callback_data='view_favorites')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_text(update: Update, context: CallbackContext) -> None:
    """Обработка текстовых сообщений."""
    log(update)
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    state = USER_STATE.get(chat_id)

    if state == 'shopping':
        processing_message = await update.message.reply_text("Ваш запрос обрабатывается, пожалуйста, подождите...")
        ingredients_list = get_ingredients_list(text)  # Получаем список продуктов от GPT
        ingredients_list_with_links = get_links_from_list(ingredients_list, config.BD_path)
        context.user_data["last_cart"] = ingredients_list_with_links

        formatted_list = "\n".join(
            [f"{i + 1}. {item['name']} - [🔗 Ссылка]({item['link']})" for i, item in
             enumerate(ingredients_list_with_links)]
        )

        await processing_message.edit_text(
            f"Ваш список продуктов готов:\n\n{formatted_list}",
            parse_mode="Markdown"
        )

        keyboard = [
            [InlineKeyboardButton("Да", callback_data='add_to_favorites')],
            [InlineKeyboardButton("Нет", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Хотите ли вы добавить эту корзину в избранное?", reply_markup=reply_markup)

        if chat_id not in PURCHASE_HISTORY:
            PURCHASE_HISTORY[chat_id] = []
        PURCHASE_HISTORY[chat_id].append(ingredients_list_with_links)

        USER_STATE[chat_id] = 'ask_favorite'

    elif state == 'naming_cart':
        if not text:
            await update.message.reply_text("Пожалуйста, введите корректное название корзины.")
            return

        if text in FAVORITES.get(chat_id, {}):
            await show_existing_cart_options(update, context, text)
            return

        last_cart = context.user_data.get("last_cart")
        if not last_cart:
            await update.message.reply_text("Ошибка: нет последней корзины для сохранения.")
            return

        if chat_id not in FAVORITES:
            FAVORITES[chat_id] = {}

        FAVORITES[chat_id][text] = last_cart
        await update.message.reply_text(f"Корзина '{text}' добавлена в избранное!")

        USER_STATE.pop(chat_id, None)
        await send_main_menu(update, context, "Могу ли я вам ещё чем-нибудь помочь?")

    else:
        await update.message.reply_text("Пожалуйста, выберите команду из меню.")


async def show_existing_cart_options(update: Update, context: CallbackContext, cart_name: str) -> None:
    """Показать варианты действий с корзиной, если имя уже существует."""
    chat_id = update.effective_chat.id
    context.user_data["current_cart_name"] = cart_name
    keyboard = [
        [InlineKeyboardButton("Просмотреть корзину", callback_data=f"view_cart:{cart_name}")],
        [InlineKeyboardButton("Отмена добавления", callback_data='cancel')],
        [InlineKeyboardButton("Выбрать другое имя для корзины", callback_data='choose_new_name')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"Корзина с именем '{cart_name}' уже существует. Пожалуйста, выберите действие.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"Корзина с именем '{cart_name}' уже существует. Пожалуйста, выберите действие.",
            reply_markup=reply_markup
        )
    USER_STATE[chat_id] = 'existing_cart_options'


async def shopping(update: Update, context: CallbackContext) -> None:
    """Обработка команды для создания корзины."""
    log(update)
    chat_id = update.effective_chat.id
    USER_STATE[chat_id] = 'shopping'
    await update.message.reply_text(
        "Вы выбрали: Составить корзину. Опишите, что хотите приготовить или введите список продуктов.")


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
    elif query.data == 'back':
        await send_main_menu(update, context, "Могу ли я вам ещё чем-нибудь помочь?")
    elif query.data == 'cancel':
        USER_STATE.pop(chat_id, None)
        await send_main_menu(update, context, "Добавление корзины отменено. Могу ли я вам ещё чем-нибудь помочь?")
    elif query.data == 'choose_new_name':
        USER_STATE[chat_id] = 'naming_cart'
        await query.edit_message_text("Как вы хотите назвать свою корзину?")
    elif query.data == 'view_favorites':
        USER_STATE[chat_id] = 'viewing_favorites'
        await send_favorites_menu(update, chat_id)
    elif query.data.startswith("view_cart:"):
        cart_name = query.data.split(":", 1)[1]
        await view_cart(update, context, cart_name, back_to_existing=True)
    elif query.data == 'show_existing_cart_options':
        cart_name = context.user_data.get("current_cart_name")
        if cart_name:
            await show_existing_cart_options(update, context, cart_name)


async def view_cart(update: Update, context: CallbackContext, cart_name: str, back_to_existing: bool = False) -> None:
    """Просмотр корзины."""
    chat_id = update.effective_chat.id
    cart = FAVORITES.get(chat_id, {}).get(cart_name)
    if cart:
        formatted_cart = "\n".join(
            [f"{i + 1}. {item['name']} - [🔗 Ссылка]({item['link']})" for i, item in enumerate(cart)]
        )
        back_callback = 'show_existing_cart_options' if back_to_existing else 'back'
        await update.callback_query.edit_message_text(
            f"Корзина '{cart_name}':\n\n{formatted_cart}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data=back_callback)]
            ]),
            parse_mode="Markdown"
        )


async def send_favorites_menu(update: Update, chat_id: int) -> None:
    """Отправка меню с избранными корзинами."""
    favorite_carts = FAVORITES.get(chat_id, {})
    if favorite_carts:
        keyboard = [
            [InlineKeyboardButton(cart_name, callback_data=f"view_cart:{cart_name}")] for cart_name in favorite_carts
        ]
        keyboard.append([InlineKeyboardButton("Назад", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Исправление: проверка на callback_query
        if update.callback_query:
            await update.callback_query.message.reply_text("Выберите корзину из избранного:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Выберите корзину из избранного:", reply_markup=reply_markup)
    else:
        if update.callback_query:
            await update.callback_query.message.reply_text("У вас нет избранных корзин. Добавьте хотя бы одну корзину.")
        else:
            await update.message.reply_text("У вас нет избранных корзин. Добавьте хотя бы одну корзину.")

        # Переход в исходное состояние с главными кнопками
        await send_main_menu(update, context, "Могу ли я вам ещё чем-нибудь помочь?")


def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(config.TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()


if __name__ == '__main__':
    main()