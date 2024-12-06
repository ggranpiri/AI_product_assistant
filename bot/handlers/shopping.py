from telegram import Update
from telegram.ext import CallbackContext
from AI_product_assistant.gpt_request import get_ingredients_list
from AI_product_assistant.parser.match_product import get_links_from_list
from AI_product_assistant.bot.utils.bot_logging import log
from AI_product_assistant.bot.states import USER_STATE, MAX_RETRIES
from AI_product_assistant.config import BD_path

async def shopping_command(update: Update, context: CallbackContext) -> None:
    """Обработка команды для создания корзины."""
    log(update)
    chat_id = update.effective_chat.id
    USER_STATE[chat_id] = 'shopping'
    await update.message.reply_text(
        "Вы выбрали: Составить корзину. Опишите, что хотите приготовить или введите список продуктов."
    )


async def handle_text(update: Update, context: CallbackContext) -> None:
    """Обработка текстовых сообщений."""
    log(update)
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if USER_STATE.get(chat_id) == 'shopping':
        await process_shopping_request(update, context, text)
    else:
        await update.message.reply_text("Пожалуйста, выберите команду из меню.")


async def process_shopping_request(update: Update, context: CallbackContext, text: str) -> None:
    """Обработка запроса для создания списка покупок."""
    processing_message = await update.message.reply_text("Ваш запрос обрабатывается, пожалуйста, подождите...")

    retries = 0
    ingredients_list = None
    while retries < MAX_RETRIES and not ingredients_list:
        try:
            ans = get_ingredients_list(text)
            dish, ingredients_list = ans["dish"], ans["ingredients"]
        except Exception as e:
            print(f"Ошибка: {e}")
        retries += 1

    if not ingredients_list:
        await processing_message.edit_text(
            "Извините, нам не удалось найти подходящие продукты. Пожалуйста, повторите ваш запрос ещё раз."
        )
        return

    ingredients_list_with_links = get_links_from_list(ingredients_list, BD_path)
    context.user_data["last_cart"] = ingredients_list_with_links
    formatted_list = format_ingredients_list(ingredients_list, ingredients_list_with_links)
    await processing_message.edit_text(
        f"Ваш список продуктов готов:\n{formatted_list}",
        parse_mode="Markdown"
    )


def format_ingredients_list(ingredients, links):
    """Форматирование списка ингредиентов."""
    result = ""
    for i, (key, item) in enumerate(zip(ingredients.keys(), links)):
        if item:
            result += f"{i + 1}. [{item['name']}]({item['link']}) - {item['packs_needed']} шт, {item['price']} ₽\n"
        else:
            result += f"{i + 1}. {key} - не удалось найти\n"
    return result
