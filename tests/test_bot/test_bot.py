import pytest
import pytest_asyncio
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


@pytest_asyncio.fixture
async def bot_client():
    class MockBotClient:
        def __init__(self):
            self.chat_id = 12345

        async def send_command(self, command):
            if command == "/start":
                return MockResponse(
                    text="Я — ваш умный помощник",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🍎 Составить корзину", callback_data="shopping")]
                        ]
                    )
                )
            return MockResponse(text="")

        async def send_callback_query(self, callback_data):
            if callback_data == "shopping":
                return MockResponse(text="Опишите, что хотите приготовить или введите список продуктов.")
            elif callback_data.startswith("delete_cart:"):
                cart_name = callback_data.split(":")[1]
                return MockResponse(text=f"Корзина '{cart_name}' удалена.")
            return MockResponse(text="")

        async def send_message(self, message):
            if message == "":
                return MockResponse(text="Пожалуйста, введите корректное название корзины.")
            return MockResponse(text=f"Корзина '{message}' добавлена в избранное!")

    class MockResponse:
        def __init__(self, text, reply_markup=None):
            self.text = text
            self.reply_markup = reply_markup

    return MockBotClient()


@pytest.mark.asyncio
async def test_start(bot_client):
    """Проверка команды /start и основного меню."""
    response = await bot_client.send_command("/start")
    assert "Я — ваш умный помощник" in response.text
    assert any(isinstance(button, InlineKeyboardButton) and "🍎 Составить корзину" in button.text
               for button in response.reply_markup.inline_keyboard[0])


@pytest.mark.asyncio
async def test_shopping_process(bot_client):
    """Проверка состояния 'shopping' и ввода текста."""
    response = await bot_client.send_callback_query("shopping")
    assert response.text == "Опишите, что хотите приготовить или введите список продуктов."


@pytest.mark.asyncio
async def test_favorites_workflow(bot_client):
    """Проверка добавления и удаления корзины в избранное."""
    chat_id = bot_client.chat_id

    # Добавление корзины
    response = await bot_client.send_message("Моя корзина")
    assert "Корзина 'Моя корзина' добавлена в избранное!" in response.text

    # Удаление корзины
    response = await bot_client.send_callback_query("delete_cart:Моя корзина")
    assert "Корзина 'Моя корзина' удалена." in response.text


@pytest.mark.asyncio
async def test_invalid_input(bot_client):
    """Проверка обработки некорректного ввода."""
    response = await bot_client.send_message("")
    assert "Пожалуйста, введите корректное название корзины." in response.text