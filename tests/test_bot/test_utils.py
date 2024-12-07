import pytest
from unittest import mock
from datetime import datetime
from AI_product_assistant.bot.utils.data_time import get_date
from AI_product_assistant.bot.utils.logger import log


# Тест для функции get_date
def test_get_date():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    assert get_date() == current_time


# Тест для функции log с update.message
def test_log_message():
    # Создаем mock для update.message
    mock_update = mock.Mock()
    mock_message = mock.Mock()
    mock_user = mock.Mock()

    mock_user.first_name = "Masha"
    mock_user.last_name = "Sasha"
    mock_user.id = 12345
    mock_message.from_user = mock_user
    mock_message.text = "Hello, world!"
    mock_update.message = mock_message

    # Мокаем функцию get_date
    with mock.patch('AI_product_assistant.bot.utils.data_time.get_date', return_value="2024-12-07 18:38:00"):
        with mock.patch('builtins.print') as mock_print:
            log(mock_update)
            # Проверяем, что печать вывела правильную информацию
            mock_print.assert_called_with("2024-12-07 18:38:00 - Masha Sasha (id 12345) написал: \"Hello, world!\"")


# Тест для функции log с update.callback_query
def test_log_callback_query():
    # Создаем mock для update.callback_query
    mock_update = mock.Mock()
    mock_query = mock.Mock()
    mock_user = mock.Mock()

    mock_user.first_name = "Masha"
    mock_user.id = 12345
    mock_query.from_user = mock_user
    mock_query.data = "SomeAction"
    mock_update.callback_query = mock_query

    # Мокаем функцию get_date
    with mock.patch('AI_product_assistant.bot.utils.data_time.get_date', return_value="2024-12-07 18:38:00"):
        with mock.patch('builtins.print') as mock_print:
            log(mock_update)
            # Проверяем, что печать вывела правильную информацию
            mock_print.assert_called_with("2024-12-07 18:38:00 - Masha (id 12345) нажал кнопку: \"SomeAction\"")


if __name__ == "__main__":
    pytest.main()
