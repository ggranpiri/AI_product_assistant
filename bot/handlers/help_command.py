from telegram import Update
from telegram.ext import CallbackContext


async def send_help(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Вот что я могу сделать:\n"
        "1. 🍎 /shopping Составить корзину - помогу подобрать продукты.\n"
        "2. 📝 /recipe Составить рецепт - помогу создать рецепт на основе продуктов.\n"
        "3. ❓ /help - Помощь.\n"
        "4. /view_favorites Просмотреть избранное - просмотрите сохранённые корзины.\n"
    )
    await update.message.reply_text(help_text)