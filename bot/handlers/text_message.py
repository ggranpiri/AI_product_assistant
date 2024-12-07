from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from AI_product_assistant.bot.handlers.buttons import send_main_menu
from AI_product_assistant.bot.utils.logger import log
from AI_product_assistant.gpt_request import get_ingredients_list
from AI_product_assistant.bot.states.user_states import USER_STATE, FAVORITES, PREV_MESSAGE, PURCHASE_HISTORY
from AI_product_assistant.parser.match_product import get_links_from_list
from AI_product_assistant.config import BD_path

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
        if not ingredients_list:
            try:
                ans = get_ingredients_list(text)
                dish, ingredients_list = ans["dish"], ans["ingredients"]
            except Exception as e:
                print(f"Ошибка: Не удалось получить корректный JSON после нескольких попыток.")


        if not ingredients_list:
            await processing_message.edit_text(
                "Извините, нам не удалось найти подходящие продукты. Пожалуйста, повторите ваш запрос еще раз."
            )
            return

        ingredients_list_with_links = get_links_from_list(ingredients_list, BD_path)
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