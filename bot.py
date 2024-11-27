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

# Обновление основного меню
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🍎 Составить корзину", callback_data='shopping')],
        [InlineKeyboardButton("Просмотреть избранное", callback_data='view_favorites')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Я — ваш умный помощник, который поможет:\n"
        "- 🛒 Составить удобный список покупок.\n"
        "- 🥗 Создать вкусный рецепт из ваших продуктов.\n\n", reply_markup=reply_markup)

# Глобальные переменные
USER_STATE = {}
FAVORITES = {}

async def handle_text(update: Update, context: CallbackContext) -> None:
    """Обработчик текстовых сообщений"""
    log(update)
    chat_id = update.effective_chat.id
    text = update.message.text

    if USER_STATE.get(chat_id) == 'shopping':
        processing_message = await update.message.reply_text("Ваш запрос обрабатывается, пожалуйста, подождите...")

        ingredients_list = get_ingredients_list(text)
        context.user_data["last_cart"] = ingredients_list  # Сохраняем корзину

        await processing_message.edit_text(f"Список продуктов: {ingredients_list}")

        # Запрашиваем добавление корзины в избранное
        keyboard = [
            [InlineKeyboardButton("Да", callback_data='add_to_favorites')],
            [InlineKeyboardButton("Нет", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Хотите ли вы добавить эту корзину в избранное?", reply_markup=reply_markup)

        USER_STATE[chat_id] = 'ask_favorite'
    else:
        await update.message.reply_text("Пожалуйста, выберите команду из меню.")

async def add_to_favorites(update: Update, context: CallbackContext) -> None:
    """Обработчик для добавления корзины в избранное."""
    log(update)
    chat_id = update.effective_chat.id
    last_cart = context.user_data.get("last_cart", None)

    if not last_cart:
        await update.message.reply_text("Вы еще не создали корзину.")
        return

    response = update.message.text.lower()

    if USER_STATE.get(chat_id) == 'ask_favorite':
        if response == 'да':
            # Если пользователь хочет добавить корзину, спрашиваем название
            await update.message.reply_text("Как вы хотите назвать свою корзину?")
            USER_STATE[chat_id] = 'naming_cart'  # Переход в состояние ожидания имени корзины
        elif response == 'нет':
            # Если пользователь не хочет добавлять корзину
            await update.message.reply_text("Корзина не была добавлена в избранное.")
            USER_STATE.pop(chat_id, None)  # Сброс состояния
        else:
            await update.message.reply_text("Пожалуйста, ответьте 'Да' или 'Нет'.")
    elif USER_STATE.get(chat_id) == 'naming_cart':
        # Обработка имени корзины
        cart_name = update.message.text.strip()
        if not cart_name:
            await update.message.reply_text("Пожалуйста, введите корректное название корзины.")
            return

        # Добавляем корзину с именем
        if chat_id not in FAVORITES:
            FAVORITES[chat_id] = {}

        FAVORITES[chat_id][cart_name] = last_cart

        await update.message.reply_text(f"Корзина '{cart_name}' добавлена в избранное!")

        # Сброс состояния после добавления корзины в избранное
        USER_STATE.pop(chat_id, None)
        await update.message.reply_text("Пожалуйста, выберите команду из меню.")



async def naming_cart(update: Update, context: CallbackContext) -> None:
    """Обработчик для задания имени корзины и добавления в избранное."""
    log(update)
    chat_id = update.effective_chat.id
    cart_name = update.message.text.strip()

    if not cart_name:
        await update.message.reply_text("Пожалуйста, введите корректное название корзины.")
        return

    last_cart = context.user_data.get("last_cart")
    if chat_id not in FAVORITES:
        FAVORITES[chat_id] = {}

    # Сохраняем корзину с названием
    FAVORITES[chat_id][cart_name] = last_cart
    await update.message.reply_text(f"Корзина '{cart_name}' добавлена в избранное!")

    # Сброс состояния
    USER_STATE.pop(chat_id, None)

async def view_favorites(update: Update, context: CallbackContext) -> None:
    """Просмотр избранных корзин."""
    log(update)
    chat_id = update.effective_chat.id
    favorites = FAVORITES.get(chat_id, {})

    if not favorites:
        await update.message.reply_text("Ваш список избранных корзин пуст.")
    else:
        favorites_list = "\n\n".join(f"Корзина '{name}':\n{cart}" for name, cart in favorites.items())
        await update.message.reply_text(f"Ваши избранные корзины:\n\n{favorites_list}")

async def shopping(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /shopping"""
    log(update)
    chat_id = update.effective_chat.id
    USER_STATE[chat_id] = 'shopping'
    keyboard = [[InlineKeyboardButton("Назад", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Вы выбрали: Составить корзину. Опишите, что хотите приготовить, или введите список продуктов.",
        reply_markup=reply_markup
    )

# Обработчик нажатий кнопок
async def button(update: Update, context: CallbackContext) -> None:
    log(update)
    query = update.callback_query
    await query.answer()

    if query.data == 'shopping':
        chat_id = query.message.chat.id
        USER_STATE[chat_id] = 'shopping'
        keyboard = [[InlineKeyboardButton("Назад", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Вы выбрали: Составить корзину. Опишите, что хотите приготовить, или введите список продуктов.",
            reply_markup=reply_markup
        )

    elif query.data == 'add_to_favorites':
        chat_id = query.message.chat.id
        last_cart = context.user_data.get("last_cart", None)
        if not last_cart:
            await query.edit_message_text("У вас еще нет созданной корзины.")
        else:
            # Спрашиваем название корзины
            await query.edit_message_text("Как вы хотите назвать свою корзину?")
            USER_STATE[chat_id] = 'naming_cart'

    elif query.data == 'back':
        keyboard = [
            [InlineKeyboardButton("🍎 Составить корзину", callback_data='shopping')],
            [InlineKeyboardButton("Просмотреть избранное", callback_data='view_favorites')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Что я могу для вас сделать?", reply_markup=reply_markup)

    elif query.data == 'view_favorites':
        chat_id = query.message.chat.id
        favorites = FAVORITES.get(chat_id, [])
        if not favorites:
            await query.edit_message_text("Ваш список избранных корзин пуст.")
        else:
            favorites_list = "\n\n".join(f"Корзина {i+1}:\n{cart}" for i, cart in enumerate(favorites))
            await query.edit_message_text(f"Ваши избранные корзины:\n\n{favorites_list}")
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


if __name__ == '__main__':
    main()