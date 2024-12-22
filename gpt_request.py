import json
from openai import OpenAI
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
    Метод позволяет обратиться к OpenAI GPT через прокси.
    ...
    (оставляем без изменений)
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
    Обрабатывает сообщение пользователя с помощью OpenAI API и возвращает кортеж:
    (название блюда, JSON со списком ингредиентов и их количеством в граммах для одной порции).
    """
    system_prompt = (
        "Ты профессиональный кулинарный помощник. Твоя задача — извлечь название блюда и сгенерировать список ингредиентов с точным количеством "
        "в граммах для ОДНОЙ порции рецепта, который описывает пользователь. Форматируй свой ответ строго в виде JSON-словаря, "
        "где первый ключ — название блюда, а значение — словарь с ингредиентами, где каждый ингредиент является ключом, а значение — списком, где первый элемент количество продукта, а второе - единица измерения.\n\n"
        "Особые инструкции:\n"
        "1. Игнорируй любые упоминания длительности или количества порций в исходном сообщении.\n"
        "2. Ответ должен строго соответствовать JSON-формату, без каких-либо пояснений и единиц измерения в значениях.\n\n"
        "Структура JSON-ответа, СТРОГО СЛЕДУЙ ЕЙ И ТОЛЬКО ЕЙ:\n"
        "{\n"
        "    \"название_блюда\": {\n"
        "        \"ингредиент1\": [количество, единица_измерения],\n"
        "        \"ингредиент2\": [количество, единица_измерения],\n"
        "        ...\n"
        "    }\n"
        "}\n\n"
        "Пример правильного ответа:\n"
        "{\n"
        "    \"борщ\": {\n"
        "        \"картофель\": [200, \"г\"],\n"
        "        \"лук репчатый\": [100, \"г\"],\n"
        "        \"свекла\": [150, \"г\"]\n"
        "    }\n"
        "}\n\n"
        "Примеры неправильных ответов:\n"
        "- Добавление пояснений вне JSON: \"Вот ваш список ингредиентов...\"\n"
        "- Использование нечисловых значений: \"соль\": \"по вкусу\"\n\n"
        "Помни, что ответ должен быть строго в формате JSON, без лишних пояснений. Подсчитай количества ингредиентов."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    for attempt in range(5):
        try:
            assistant_message = ask_gpt_with_proxy(messages, temperature=0.2)
            data = json.loads(assistant_message)

            # Проверка структуры JSON
            if isinstance(data, dict) and len(data) == 1:
                dish, ingredients = next(iter(data.items()))
                if isinstance(ingredients, dict) and all(
                        isinstance(v, list) and len(v) == 2 and isinstance(v[0], (int, float)) for v in
                        ingredients.values()
                ):
                    return {"dish": dish, "ingredients": ingredients}
            raise ValueError("JSON имеет некорректную структуру.")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Попытка {attempt + 1}: Некорректный ответ. Ошибка: {e}")
            messages.append({
                "role": "user",
                "content": (
                    "Ваш предыдущий ответ не соответствует требуемому формату. Пожалуйста, предоставьте ответ строго "
                    "в формате JSON, где первый ключ — название блюда, а значения — словарь ингредиентов с их количествами и единицами измерения. Ответ без пояснений."
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

        # Этап 2: Получение ингредиентов и названия блюда
        result = get_ingredients_per_portion(user_message)
        print(f"Название блюда: {result['dish']}")
        print(f"Ингредиенты на одну порцию: {result['ingredients']}")

        # Этап 3: Умножение на количество порций
        total_ingredients = {ingredient: [amount[0] * portions, amount[1]] for ingredient, amount in
                             result['ingredients'].items()}

        return {"dish": result['dish'], "ingredients": total_ingredients}

    except ValueError as e:
        print(f"Ошибка: {e}")
        return {"error": str(e)}


def get_preparation_instructions(dish: str, ingredients: dict) -> str:
    """
    Генерирует инструкцию по приготовлению блюда на основе названия блюда.

    :param dish: Название блюда.
    :param ingredients: Словарь с ингредиентами и их количеством.
    :return: Инструкция по приготовлению.
    """
    system_prompt = (
        "Ты профессиональный кулинарный помощник. Твоя задача — предоставить подробную и понятную инструкцию "
        "по приготовлению блюда на основе названия блюда.\n\n"
        f"Блюдо: {dish}\n"
        "Ингредиенты:\n"
    )

    user_prompt = system_prompt + "\n\n" + "Предоставь пошаговую инструкцию по приготовлению этого блюда."

    messages = [
        {"role": "system", "content": "Ты профессиональный кулинарный помощник."},
        {"role": "user", "content": user_prompt}
    ]

    for attempt in range(5):
        try:
            response = ask_gpt_with_proxy(messages, temperature=0.3, max_tokens=1000)
            if response:
                return response
            else:
                raise ValueError("Пустой ответ от модели.")
        except Exception as e:
            logger.warning(f"Попытка {attempt + 1}: Не удалось получить инструкцию по приготовлению. Ошибка: {e}")
            messages.append({
                "role": "user",
                "content": "Пожалуйста, предоставь пошаговую инструкцию по приготовлению блюда без дополнительных комментариев."
            })
    raise ValueError("Не удалось получить инструкцию по приготовлению после нескольких попыток.")


# Пример использования новой функции
if __name__ == "__main__":
    user_input = "Борщ на 4 порции"

    # Получаем название блюда и список ингредиентов
    result = get_ingredients_list(user_input)
    print(result)
    if "error" not in result:
        dish = result["dish"]
        ingredients = result["ingredients"]

        # Получаем инструкцию по приготовлению
        try:
            instructions = get_preparation_instructions(dish, ingredients)
            print(f"Инструкция по приготовлению {dish}:\n{instructions}")
        except ValueError as e:
            print(f"Ошибка при получении инструкции: {e}")
    else:
        print(f"Ошибка при получении ингредиентов: {result['error']}")