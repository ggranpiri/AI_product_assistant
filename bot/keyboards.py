from telegram import InlineKeyboardButton

def main_menu_keyboard(chat_id):
    """Клавиатура главного меню."""
    return [
        [InlineKeyboardButton("🛒 Составить корзину", callback_data="shopping")],
        [InlineKeyboardButton("⭐️ Избранное", callback_data="view_favorites")],
    ]

def favorites_menu_keyboard(chat_id):
    """Клавиатура меню избранного."""
    return [
        [InlineKeyboardButton("Добавить в избранное", callback_data="add_favorites")],
        [InlineKeyboardButton("Удалить из избранного", callback_data="remove_favorites")],
        [InlineKeyboardButton("Назад в главное меню", callback_data="main_menu")],
    ]
