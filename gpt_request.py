import json
from openai import (OpenAI)
import httpx
import config
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ask_gpt_with_proxy(messages: list,
                       max_tokens: int = None, temperature: float = 0.2,
                       model: str = "gpt-4o",
                       proxy_auth: bool = True) -> str:
    """
    Метод позволяет обратиться к OpenAI GPT через прокси.\n
    В конфиге config/config.py должны быть указаны:\n
    Данные о прокси\n
    HTTPS_PROXY_LOGIN - логин от прокси.\n
    Если необходима авторизация:\n
    HTTPS_PROXY_PASSWORD - пароль от прокси.\n
    HTTPS_PROXY_IPPORT - IP и порт прокси (например 12.345.678.900:1234)\n\n

    Данные от OpenAI\n
    OPENAI_API_KEY - API ключ от OpenAI\n

    :param messages: История сообщений (роли: system, assistant, user) - обязательный параметр.
    :param max_tokens: Максимальное количество токенов в ответе (по умолчанию None).
    :param temperature: Температура для ответа (по умолчанию 1).
    :param model: Название модели, к которой необходимо обратиться (по умолчанию "gpt-4o-mini")
    :param proxy_auth: True - необходима авторизация прокси, False - не нужна (по умолчанию False)
    :return: Ответ модели.
    """

    proxy_url = f"http://{config.HTTPS_PROXY_IPPORT}"
    if proxy_auth:
        proxy_url = f"http://{config.HTTPS_PROXY_LOGIN}:{config.HTTPS_PROXY_PASSWORD}@{config.HTTPS_PROXY_IPPORT}"

    with httpx.Client(proxy=proxy_url) as httpx_client:
        gpt_client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            http_client=httpx_client
        )

        response = gpt_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content.strip()

def get_number_of_portions(user_message: str) -> int:
    """
    Определяет количество порций из сообщения пользователя.
    """
    system_prompt = (
        "Ты профессиональный кулинарный помощник. Пользователь может указать блюдо и длительность приготовления (например, "
        "\"борщ на две недели\"). Твоя задача определить количество порций, соответствующее указанной длительности. "
        "Если длительность не указана, предположи, что требуется одна порция.\n\n"
        "Ответь только числом (целым) без дополнительных пояснений."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    for attempt in range(5):
        try:
            response = ask_gpt_with_proxy(messages, temperature=0.0)
            portions = int(response.strip())
            if portions > 0:
                return portions
            else:
                raise ValueError("Количество порций должно быть положительным.")
        except (ValueError, TypeError):
            messages.append({
                "role": "user",
                "content": "Пожалуйста, укажи количество порций как целое число."
            })
    raise ValueError("Не удалось определить количество порций после нескольких попыток.")

def get_ingredients_per_portion(user_message: str) -> dict:
    """
    Обрабатывает сообщение пользователя с помощью OpenAI API и возвращает JSON со списком ингредиентов и их количеством в граммах для одной порции.
    """
    system_prompt = (
        "Ты профессиональный кулинарный помощник. Твоя задача — генерировать список ингредиентов с точным количеством "
        "в граммах для ОДНОЙ порции рецепта, который описывает пользователь. Форматируй свой ответ строго в виде JSON-словаря, "
        "где каждый ингредиент является ключом, а значение — списком, где первый элемент кол-во продукта, а второе - единица ихмерения.\n\n"
        "Особые инструкции:\n"
        "1. Игнорируй любые упоминания длительности или количества порций в исходном сообщении.\n"
        "2. Ответ должен строго соответствовать JSON-формату, без каких-либо пояснений и единиц измерения в значениях.\n\n"
        "Структура JSON-ответа, СТРОГО СЛЕДУЙ ЕЙ И ТОЛЬКО ЕЙ:\n"
        "{\n"
        "    \"ingredient1\": [amount_in_grams, unit_of_measurement],\n"
        "    \"ingredient2\": [amount_in_grams, unit_of_measurement],\n"
        "    ...\n"
        "}\n\n"
        "Пример правильного ответа:\n"
        "{\n"
        "    \"картофель\": [1, кг],\n"
        "    \"лук репчатый\": [2, шт],\n"
        "    \"молоко\": [500, мл]\n"
        "}\n\n"
        "Примеры неправильных ответов:\n"
        "- Добавление пояснений вне JSON: \"Вот ваш список ингредиентов...\"\n"
        "- Использование нечисловых значений: \"соль\": \"по вкусу\"\n\n"
        "Помни, что ответ должен быть строго в формате JSON, без лишних пояснений. Подсчитай количества ингредиентов "
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    for attempt in range(5):
        try:
            assistant_message = ask_gpt_with_proxy(messages, temperature=0.2)
            ingredients_json = json.loads(assistant_message)

            # Проверка, что это словарь и все значения - целые числа
            if isinstance(ingredients_json, dict) and all(isinstance(v[0], int) for v in ingredients_json.values()):
                return ingredients_json
            else:
                raise ValueError("JSON содержит некорректные данные.")
        except (json.JSONDecodeError, ValueError, TypeError):
            messages.append({
                "role": "user",
                "content": (
                    "Ваш предыдущий ответ не соответствует требуемому формату. Пожалуйста, предоставьте ответ строго "
                    "в формате JSON-словаря, где значения список из двух элементов, кол-во продукта и единица измерения. Ответ без пояснений."
                )
            })
    raise ValueError("Не удалось получить корректный JSON после нескольких попыток.")

def get_ingredients_list(user_message: str) -> dict:
    """
    Обрабатывает сообщение пользователя и возвращает JSON со списком ингредиентов и их количеством в граммах.
    """
    try:
        # Этап 1: Определение количества порций
        portions = get_number_of_portions(user_message)
        print(f"Количество порций: {portions}")

        # Этап 2: Получение ингредиентов на одну порцию
        ingredients_per_portion = get_ingredients_per_portion(user_message)
        print(f"Ингредиенты на одну порцию: {ingredients_per_portion}")

        # Этап 3: Умножение на количество порций
        total_ingredients = {ingredient: [amount[0] * portions, amount[1]] for ingredient, amount in ingredients_per_portion.items()}

        return total_ingredients

    except ValueError as e:
        print(f"Ошибка: {e}")
        return {"error": str(e)}