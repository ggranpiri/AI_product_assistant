import pytest
from unittest import mock
from telegram import Update
from telegram import CallbackQuery
from unittest.mock import MagicMock, AsyncMock
from AI_product_assistant.bot.handlers.buttons import button
from AI_product_assistant.bot.handlers.favorites import send_favorites_menu
from AI_product_assistant.bot.states.user_states import FAVORITES
from AI_product_assistant.bot.handlers.buttons import send_main_menu


@pytest.mark.asyncio
async def test_send_main_menu_with_favorites():
    update = MagicMock(Update)
    update.effective_chat.id = 12345
    update.callback_query = None
    update.message.reply_text = AsyncMock()

    # Мокаем get_date для получения фиксированной даты
    with mock.patch('AI_product_assistant.bot.utils.data_time.get_date', return_value="2024-12-07 18:38:00"):
        # Теперь передаем аргумент text
        await send_main_menu(update, mock.MagicMock(), "Some text")


@pytest.mark.asyncio
async def test_send_main_menu_without_favorites():
    update = MagicMock(Update)
    update.effective_chat.id = 12345
    update.callback_query = None
    update.message.reply_text = AsyncMock()

    # Мокаем get_date для получения фиксированной даты
    with mock.patch('AI_product_assistant.bot.utils.data_time.get_date', return_value="2024-12-07 18:38:00"):
        # Теперь передаем аргумент text
        await send_main_menu(update, mock.MagicMock(), "Some text")


@pytest.mark.asyncio
async def test_button_shopping():
    update = MagicMock(Update)
    query = MagicMock(CallbackQuery)
    query.data = 'shopping'
    query.message.chat.id = 12345
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()

    update.callback_query = query
    # Теперь можно использовать await с AsyncMock
    await button(update, mock.MagicMock())


@pytest.mark.asyncio
async def test_button_view_favorites():
    update = MagicMock(Update)
    query = MagicMock(CallbackQuery)
    query.data = 'view_favorites'
    query.message.chat.id = 12345
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()

    update.callback_query = query
    # Теперь можно использовать await с AsyncMock
    await button(update, mock.MagicMock())


@pytest.mark.asyncio
async def test_button_delete_cart():
    update = MagicMock(Update)
    query = MagicMock(CallbackQuery)
    query.data = 'delete_cart:cart1'
    query.message.chat.id = 12345
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()

    update.callback_query = query
    # Теперь можно использовать await с AsyncMock
    await button(update, mock.MagicMock())


@pytest.mark.asyncio
async def test_send_favorites_menu_with_items():
    update = MagicMock(Update)
    update.effective_chat.id = 12345
    update.callback_query = None
    update.message.reply_text = AsyncMock()

    FAVORITES[12345] = {'cart1': ['item1', 'item2']}

    await send_favorites_menu(update, mock.MagicMock())


@pytest.mark.asyncio
async def test_send_favorites_menu_empty():
    FAVORITES.clear()

    update = MagicMock(Update)
    update.effective_chat.id = 12345
    update.callback_query = None
    update.message.reply_text = AsyncMock()

    await send_favorites_menu(update, mock.MagicMock())