from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters
import config
from gpt_request import get_ingredients_list
import logging

# Отключение логирования для библиотеки httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

def get_date() -> str:
    """Получение текущей даты и времени в формате строки."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Настройка логирования
def log(update: Update) -> None:
    """Логирование имени пользователя и его действий (сообщений или нажатий кнопок)."""
    if update.message:  # Если пользователь отправил текстовое сообщение
        user = update.message.from_user
        name = f"{user.first_name} {user.last_name or ''}".strip()
        text = update.message.text
        print(f'{get_date()} - {name} (id {user.id}) написал: "{text}"')

    elif update.callback_query:  # Если пользователь нажал на кнопку
        query = update.callback_query
        user = query.from_user
        action = query.data
        print(f'{get_date()} - {user.first_name} (id {user.id}) нажал кнопку: "{action}"')

    else:
        print(f"{get_date()} - system_log: Неизвестное действие")


# Функция старта
async def start(update: Update, context: CallbackContext) -> None:
    # Главное меню с кнопками
    keyboard = [
        [InlineKeyboardButton("🍎 Составить корзину", callback_data='basket')],
        [InlineKeyboardButton("🍳 Составить рецепт", callback_data='recipe')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Я — ваш умный помощник, который поможет:\n"
        "- 🛒 Составить удобный список покупок.\n"
        "- 🥗 Создать вкусный рецепт из ваших продуктов.\n\n", reply_markup=reply_markup)


# Глобальная переменная для сохранения текущего состояния пользователя
USER_STATE = {}

async def handle_text(update: Update, context: CallbackContext) -> None:
    """Обработчик текстовых сообщений"""
    log(update)
    chat_id = update.effective_chat.id
    text = update.message.text

    if USER_STATE.get(chat_id) == 'shopping':
        # Отправляем текст в функцию GPT для обработки
        ingredients_list = get_ingredients_list(text)
        await update.message.reply_text(f"Список продуктов: {ingredients_list}")
        # Сбрасываем состояние
        USER_STATE.pop(chat_id, None)
    else:
        await update.message.reply_text("Пожалуйста, выберите команду из меню.")

# Обработка команд через меню BotFather
async def shopping(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /shopping"""
    log(update)
    chat_id = update.effective_chat.id
    USER_STATE[chat_id] = 'shopping'
    await update.message.reply_text("Опишите что хотите приготовить или список продуктов для заказа")



async def recipe(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /recipe"""
    await update.message.reply_text("Вы выбрали: Составить рецепт. Из каких продуктов вы хотите сделать блюдо?")


# Обработка нажатий на кнопки в меню
async def button(update: Update, context: CallbackContext) -> None:
    log(update)
    query = update.callback_query
    await query.answer()

    if query.data == 'basket':
        # Бот спрашивает у пользователя, какие продукты он хочет добавить в корзину
        await query.edit_message_text(text="Вы выбрали: Составить корзину. Какие продукты вам нужны?")

    elif query.data == 'recipe':
        # Бот спрашивает, какие продукты нужны для рецепта
        await query.edit_message_text(text="Вы выбрали: Составить рецепт. Из каких продуктов вы хотите сделать блюдо?")

    else:
        await query.edit_message_text(text="Неизвестный выбор.")


# Основная функция для запуска бота
def main() -> None:
    # Создание приложения (вместо Updater)
    print("Запуск...")
    application = Application.builder().token(config.TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("shopping", shopping))
    application.add_handler(CommandHandler("recipe", recipe))

    # Регистрация обработчика нажатий на кнопки
    application.add_handler(CallbackQueryHandler(button))

    # Регистрация обработчика текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
