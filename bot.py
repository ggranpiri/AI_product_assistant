from datetime import datetime

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
PREV_MESSAGE = {}

MAX_RETRIES = 3


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


async def handle_text(update: Update, context: CallbackContext) -> None:
    """Обработка текстовых сообщений."""
    log(update)
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    state = USER_STATE.get(chat_id)

    if state == 'shopping':
        processing_message = await update.message.reply_text("Ваш запрос обрабатывается, пожалуйста, подождите...")

        retries = 0
        ingredients_list = None
        while retries < MAX_RETRIES and not ingredients_list:
            try:
                ingredients_list = get_ingredients_list(text)
            except Exception as e:
                print(f"Ошибка: {e}")
            retries += 1

        if not ingredients_list:
            await processing_message.edit_text(
                "Извините, нам не удалось найти подходящие продукты. Пожалуйста, повторите ваш запрос еще раз."
            )
            return

        ingredients_list_with_links = get_links_from_list(ingredients_list, config.BD_path)
        context.user_data["last_cart"] = ingredients_list_with_links

        if not ingredients_list_with_links:
            await processing_message.edit_text(
                "Извините, нам не удалось вам помочь. Пожалуйста, повторите ваш запрос еще раз."
            )
            return

        total_price = sum(item.get('price', 0) for item in ingredients_list_with_links)
        formatted_list = ""
        for i, key in enumerate(ingredients_list.keys()):
            item = ingredients_list_with_links[i]
            if not item:
                formatted_list += f"{i + 1}. {key} - не удалось найти\n"
            else:
                formatted_list += f"{i + 1}. [{item['name']}]({item['link']}) - {item['packs_needed']} шт, {item['price']} ₽\n"
        print(formatted_list)
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

        if chat_id not in PURCHASE_HISTORY:
            PURCHASE_HISTORY[chat_id] = []
        PURCHASE_HISTORY[chat_id].append(ingredients_list_with_links)

        USER_STATE[chat_id] = 'ask_favorite'
        PREV_MESSAGE[chat_id] = formatted_list

    elif state == 'naming_cart':
        if not text:
            await update.message.reply_text("Пожалуйста, введите корректное название корзины.")
            return

        if chat_id in FAVORITES and text in FAVORITES[chat_id]:
            USER_STATE[chat_id] = 'naming_conflict'
            keyboard = [
                [InlineKeyboardButton("Выбрать другое имя", callback_data='choose_another_name')],
                [InlineKeyboardButton("Отмена добавления", callback_data='cancel_addition')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Корзина с именем '{text}' уже существует. Выберите одно из действий:",
                reply_markup=reply_markup
            )
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


async def send_favorites_menu(update: Update, context: CallbackContext) -> None:
    """Отправка меню с избранными корзинами."""
    chat_id = update.effective_chat.id
    favorite_carts = FAVORITES.get(chat_id, {})

    if not favorite_carts:
        await update.callback_query.edit_message_text("У вас пока нет избранных корзин.")
        return

    keyboard = [[InlineKeyboardButton(cart_name, callback_data=f"view_cart:{cart_name}")]
                for cart_name in favorite_carts]
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Ваши избранные корзины:", reply_markup=reply_markup)


def main() -> None:
    """Основной запуск бота."""
    application = Application.builder().token(config.TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("shopping", shopping))

    application.run_polling()


if __name__ == '__main__':
    main()