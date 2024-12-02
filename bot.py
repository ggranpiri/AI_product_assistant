import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import config
from gpt_request import get_ingredients_list
from parser import get_links_from_list

# Уровень логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Состояния
MENU, SHOPPING, ASK_FAVORITE, NAMING_CART, VIEW_FAVORITES, FAVORITE_DETAILS = range(6)

# Хранилище избранных корзин
FAVORITES = {}


def get_date() -> str:
    """Получить текущую дату."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Стартовая команда, отправка главного меню."""
    logger.info(f"Пользователь {update.effective_user.id} начал работу с ботом.")
    await send_main_menu(update, context, "Привет! Я ваш помощник для создания списков покупок.")
    return MENU


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Отправить главное меню с кнопками."""
    keyboard = [
        [InlineKeyboardButton("🍎 Составить корзину", callback_data=str(SHOPPING))],
        [InlineKeyboardButton("📌 Просмотреть избранное", callback_data=str(VIEW_FAVORITES))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def shopping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрос на создание корзины."""
    logger.info(f"Пользователь {update.effective_user.id} начал создавать корзину.")
    await update.callback_query.edit_message_text("Опишите, что хотите приготовить, или введите список продуктов.")
    return SHOPPING


async def handle_shopping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка текста для создания корзины."""
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    processing_message = await update.message.reply_text("Обрабатываю запрос...")

    try:
        ingredients_list = get_ingredients_list(text)
        ingredients_with_links = get_links_from_list(ingredients_list, config.BD_path)
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        await processing_message.edit_text("Произошла ошибка. Попробуйте снова.")
        return MENU

    context.user_data["last_cart"] = ingredients_with_links

    cart_text = "\n".join(
        [f'<a href="{product["link"]}">{product["name"]}</a>' for product in ingredients_with_links]
    )
    await processing_message.edit_text(f"Список продуктов:\n{cart_text}", parse_mode="HTML")

    keyboard = [
        [InlineKeyboardButton("Да", callback_data=str(ASK_FAVORITE))],
        [InlineKeyboardButton("Нет", callback_data=str(MENU))],
    ]
    await update.message.reply_text(
        "Хотите ли вы добавить эту корзину в избранное?", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_FAVORITE


async def add_to_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрос на сохранение корзины в избранное."""
    await update.callback_query.edit_message_text("Как вы хотите назвать свою корзину?")
    return NAMING_CART


async def naming_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохранение корзины в избранное с названием."""
    chat_id = update.effective_chat.id
    cart_name = update.message.text.strip()
    last_cart = context.user_data.get("last_cart")

    if not last_cart:
        await update.message.reply_text("Ошибка: нет последней корзины для сохранения.")
        return MENU

    FAVORITES.setdefault(chat_id, {})[cart_name] = last_cart
    await update.message.reply_text(f"Корзина '{cart_name}' добавлена в избранное!")
    await send_main_menu(update, context, "Чем ещё могу помочь?")
    return MENU


async def view_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Просмотр избранных корзин."""
    chat_id = update.effective_chat.id
    favorites = FAVORITES.get(chat_id, {})
    if not favorites:
        await update.callback_query.edit_message_text("Ваш список избранного пуст.")
        return MENU

    keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in favorites.keys()]
    keyboard.append([InlineKeyboardButton("Назад", callback_data=str(MENU))])

    await update.callback_query.edit_message_text(
        "Ваши избранные корзины:", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return FAVORITE_DETAILS


async def favorite_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Просмотр содержимого избранной корзины."""
    chat_id = update.effective_chat.id
    cart_name = update.callback_query.data
    cart = FAVORITES.get(chat_id, {}).get(cart_name)

    if not cart:
        await update.callback_query.edit_message_text("Ошибка: корзина не найдена.")
        return MENU

    cart_text = "\n".join(
        [f'<a href="{product["link"]}">{product["name"]}</a>' for product in cart]
    )
    keyboard = [[InlineKeyboardButton("Назад", callback_data=str(VIEW_FAVORITES))]]
    await update.callback_query.edit_message_text(
        f"Корзина *{cart_name}*:\n{cart_text}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
    )
    return VIEW_FAVORITES


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возврат в главное меню."""
    await send_main_menu(update, context, "Главное меню")
    return MENU


def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(config.TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                CallbackQueryHandler(shopping, pattern=f"^{SHOPPING}$"),
                CallbackQueryHandler(view_favorites, pattern=f"^{VIEW_FAVORITES}$"),
            ],
            SHOPPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_shopping)],
            ASK_FAVORITE: [
                CallbackQueryHandler(add_to_favorites, pattern=f"^{ASK_FAVORITE}$"),
                CallbackQueryHandler(back_to_menu, pattern=f"^{MENU}$"),
            ],
            NAMING_CART: [MessageHandler(filters.TEXT & ~filters.COMMAND, naming_cart)],
            VIEW_FAVORITES: [
                CallbackQueryHandler(favorite_details),
                CallbackQueryHandler(back_to_menu, pattern=f"^{MENU}$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conversation_handler)
    application.run_polling()


if __name__ == "__main__":
    main()