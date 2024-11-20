import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# Функция старта
async def start(update: Update, context: CallbackContext) -> None:
    # Главное меню с кнопками
    keyboard = [
        [InlineKeyboardButton("Составить корзину", callback_data='basket')],
        [InlineKeyboardButton("Составить рецепт", callback_data='recipe')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Я — умный помощник для составления продуктовой корзины или кулинарного рецепта.", reply_markup=reply_markup)


# Обработка команд через меню BotFather
async def shopping(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /shopping"""
    await update.message.reply_text("Вы выбрали: Составить корзину. Какие продукты вам нужны?")


async def recipe(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /recipe"""
    await update.message.reply_text("Вы выбрали: Составить рецепт. Из каких продуктов вы хотите сделать блюдо?")


# Обработка нажатий на кнопки в меню
async def button(update: Update, context: CallbackContext) -> None:
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
    token = '7762120638:AAEn-KaM6kWue3UZVqNMtHz8VrChQGeRIO0' 

    # Создание приложения (вместо Updater)
    application = Application.builder().token(token).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("shopping", shopping))
    application.add_handler(CommandHandler("recipe", recipe))

    # Регистрация обработчика нажатий на кнопки
    application.add_handler(CallbackQueryHandler(button))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
