from telegram import Update
from telegram.ext import CallbackContext

from bot.handlers.buttons import send_main_menu
from bot.handlers.handle_format import format_recipe_ingredients
from bot.states.user_states import USER_STATE
from gpt_request import get_ingredients_list, get_preparation_instructions
from parser.match_product import get_links_from_list
from config import BD_path


async def process_recipe(update: Update, context: CallbackContext, text: str, chat_id: int) -> None:
    """Обработка состояния 'recipe'."""
    result = get_ingredients_list(text)

    if "error" in result:
        await update.message.reply_text(
            "Извините, нам не удалось вам помочь. Пожалуйста, повторите ваш запрос еще раз.")
        return

    dish, ingredients = result['dish'], result['ingredients']
    ingredients_list_with_links = get_links_from_list(ingredients, BD_path)


    formatted_list = format_recipe_ingredients(ingredients, ingredients_list_with_links)

    try:
        instructions = get_preparation_instructions(dish, ingredients)
    except ValueError as e:
        await update.message.reply_text(f"Ошибка при получении инструкции: {e}")
        return

    final_message = f"{formatted_list}\n*Рецепт для {dish}:*\n\n*Инструкция по приготовлению:*\n\n{instructions}"
    await update.message.reply_text(final_message, parse_mode="Markdown")

    await send_main_menu(update, context, "Могу ли я вам ещё чем-нибудь помочь?")
    USER_STATE[chat_id] = None

def fetch_ingredients_list(text: str):
    """Получение списка ингредиентов."""
    try:
        ans = get_ingredients_list(text)
        return ans["ingredients"]
    except Exception:
        print("Ошибка: Не удалось получить корректный JSON после нескольких попыток.")
        return None

