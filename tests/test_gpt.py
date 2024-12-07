import pytest
from unittest.mock import patch, MagicMock
from AI_product_assistant.gpt_request import ask_gpt_with_proxy


def test_ask_gpt_with_proxy():
    # Мокируем ответ от OpenAI API
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]

    # Мокаем OpenAI и httpx.Client
    with patch('AI_product_assistant.gpt_request.OpenAI') as MockOpenAI, \
            patch('AI_product_assistant.gpt_request.httpx.Client') as MockHttpClient:
        # Настроим мок на возврат нужного ответа
        MockOpenAI.return_value.chat.completions.create.return_value = mock_response

        # Даем параметры для теста
        messages = [{"role": "user", "content": "Test"}]

        # Настроим переменные окружения или конфиг для прокси (это важно для теста)
        proxy_url = "http://testuser:testpass@168.228.47.39:9023"  # Пример адреса с логином и паролем
        with patch('AI_product_assistant.gpt_request.config.HTTPS_PROXY_IPPORT', '168.228.47.39:9023'), \
                patch('AI_product_assistant.gpt_request.config.HTTPS_PROXY_LOGIN', 'testuser'), \
                patch('AI_product_assistant.gpt_request.config.HTTPS_PROXY_PASSWORD', 'testpass'):
            result = ask_gpt_with_proxy(messages)

        # Проверяем, что результат это строка
        assert isinstance(result, str)
        assert result == "Test response"

        # Проверяем, что прокси используется правильно
        MockHttpClient.assert_called_once_with(proxy=proxy_url)
        MockOpenAI.assert_called_once()