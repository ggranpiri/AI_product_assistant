from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters
import config
from gpt_request import get_ingredients_list
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)

def get_date() -> str:
    """Получение текущей даты и времени в формате строки."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Логирование
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

# Глобальные переменные
USER_STATE = {}
FAVORITES = {}
ORDER_HISTORY = {}

# Функции для взаимодействия с пользователем
async def start(update: Update, context: CallbackContext) -> None:
    """Приветственное сообщение и главное меню."""
    log(update)
    keyboard = [
        [InlineKeyboardButton("🍎 Составить корзину", callback_data='shopping')],
        [InlineKeyboardButton("Просмотреть избранное", callback_data='view_favorites')],
        [InlineKeyboardButton("История заказов", callback_data='order_history')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Я — ваш умный помощник, который поможет:\n"
        "- 🛒 Составить удобный список покупок.\n"
        "- 🥗 Создать вкусный рецепт из ваших продуктов.\n\n", reply_markup=reply_markup)

async def shopping(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /shopping."""
    log(update)
    chat_id = update.effective_chat.id
    USER_STATE[chat_id] = 'shopping'

    keyboard = [[InlineKeyboardButton("Назад", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "Вы выбрали: Составить корзину. Опишите, что хотите приготовить, или введите список продуктов.",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            "Вы выбрали: Составить корзину. Опишите, что хотите приготовить, или введите список продуктов.",
            reply_markup=reply_markup
        )

async def view_favorites(update: Update, context: CallbackContext) -> None:
    """Просмотр избранных корзин."""
    log(update)
    chat_id = update.effective_chat.id
    favorites = FAVORITES.get(chat_id, {})
    if not favorites:
        await update.message.reply_text("Ваш список избранных корзин пуст.")
    else:
        favorites_list = "\n\n".join(f"Корзина '{name}':\n{cart}" for name, cart in favorites.items())
        keyboard = [
            [InlineKeyboardButton("🔁 Повторить заказ", callback_data='repeat_order')],
            [InlineKeyboardButton("🗑 Удалить корзину", callback_data='delete_cart')],
            [InlineKeyboardButton("✏️ Переименовать корзину", callback_data='rename_cart')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Ваши избранные корзины:\n\n{favorites_list}", reply_markup=reply_markup)

async def handle_text(update: Update, context: CallbackContext) -> None:
    """Обработка текстовых сообщений."""
    log(update)
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    state = USER_STATE.get(chat_id)

    if state == 'shopping':
        # Создание корзины
        processing_message = await update.message.reply_text("Ваш запрос обрабатывается, пожалуйста, подождите...")
        ingredients_list = get_ingredients_list(text)
        context.user_data["last_cart"] = ingredients_list  # Сохраняем корзину

        await processing_message.edit_text(f"Список продуктов: {ingredients_list}")

        # Запрос добавления корзины в избранное
        keyboard = [
            [InlineKeyboardButton("Да", callback_data='add_to_favorites')],
            [InlineKeyboardButton("Нет", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Хотите ли вы добавить эту корзину в избранное?", reply_markup=reply_markup)
        USER_STATE[chat_id] = 'ask_favorite'

    elif state == 'naming_cart':
        # Присвоение имени корзине
        last_cart = context.user_data.get("last_cart")
        if not last_cart:
            await update.message.reply_text("Ошибка: корзина не найдена. Попробуйте снова.")
            USER_STATE.pop(chat_id, None)
            return

        if not text:
            await update.message.reply_text("Пожалуйста, введите корректное название корзины.")
            return

        if chat_id not in FAVORITES:
            FAVORITES[chat_id] = {}

        FAVORITES[chat_id][text] = last_cart
        await update.message.reply_text(f"Корзина '{text}' добавлена в избранное!")
        USER_STATE.pop(chat_id, None)

    else:
        await update.message.reply_text("Пожалуйста, выберите команду из меню.")

async def button(update: Update, context: CallbackContext) -> None:
    log(update)
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    if query.data == 'shopping':
        await shopping(update, context)

    elif query.data == 'add_to_favorites':
        last_cart = context.user_data.get("last_cart", None)
        if not last_cart:
            await query.edit_message_text("У вас еще нет созданной корзины.")
        else:
            await query.edit_message_text("Как вы хотите назвать свою корзину?")
            USER_STATE[chat_id] = 'naming_cart'

    elif query.data == 'view_favorites':
        await view_favorites(update, context)

    elif query.data == 'repeat_order':
        # Повторить заказ
        favorites = FAVORITES.get(chat_id, {})
        if not favorites:
            await query.edit_message_text("У вас нет избранных корзин для повторения.")
        else:
            await query.edit_message_text("Выберите корзину для повторного заказа.")

    elif query.data == 'delete_cart':
        # Удалить корзину
        favorites = FAVORITES.get(chat_id, {})
        if not favorites:
            await query.edit_message_text("У вас нет корзин для удаления.")
        else:
            cart_name = query.message.text.split("\n")[0].split(" ")[1].strip("'")  # Извлекаем название корзины
            if cart_name in favorites:
                del favorites[cart_name]
                await query.edit_message_text(f"Корзина '{cart_name}' удалена.")
            else:
                await query.edit_message_text("Корзина не найдена.")

    elif query.data == 'rename_cart':
        # Переименовать корзину
        favorites = FAVORITES.get(chat_id, {})
        if not favorites:
            await query.edit_message_text("У вас нет корзин для переименования.")
        else:
            cart_name = query.message.text.split("\n")[0].split(" ")[1].strip("'")
            if cart_name in favorites:
                await query.edit_message_text(f"Как вы хотите переименовать корзину '{cart_name}'?")
                USER_STATE[chat_id] = 'naming_cart'
            else:
                await query.edit_message_text("Корзина не найдена.")

    elif query.data == 'back':
        keyboard = [
            [InlineKeyboardButton("🍎 Составить корзину", callback_data='shopping')],
            [InlineKeyboardButton("Просмотреть избранное", callback_data='view_favorites')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Что я могу для вас сделать?", reply_markup=reply_markup)

    else:
        await query.edit_message_text("Неизвестный выбор.")

# Основная функция
def main() -> None:
    print("Запуск...")
    application = Application.builder().token(config.TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("shopping", shopping))
    application.add_handler(CommandHandler("view_favorites", view_favorites))

    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()

if __name__ == "__main__":
    main()