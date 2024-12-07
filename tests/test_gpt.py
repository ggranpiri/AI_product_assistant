import pytest
from unittest.mock import patch, MagicMock
import json
from gpt_request import (
    get_number_of_portions,
    get_ingredients_per_portion,
    get_ingredients_list,
    get_preparation_instructions
)


# Фикстура для мока ответа от OpenAI API
@pytest.fixture
def mock_ask_gpt_with_proxy():
    with patch('gpt_request.ask_gpt_with_proxy') as mock:
        yield mock


# Тест функции get_number_of_portions
def test_get_number_of_portions_success(mock_ask_gpt_with_proxy):
    # Настройка мока для успешного ответа
    mock_ask_gpt_with_proxy.return_value = "4"

    user_message = "Борщ на 4 порции"
    portions = get_number_of_portions(user_message)

    assert portions == 4
    mock_ask_gpt_with_proxy.assert_called()


def test_get_number_of_portions_invalid_response(mock_ask_gpt_with_proxy):
    # Настройка мока для некорректного ответа
    mock_ask_gpt_with_proxy.side_effect = ["invalid", "0", "-1", "2"]

    user_message = "Борщ"
    portions = get_number_of_portions(user_message)

    assert portions == 2
    assert mock_ask_gpt_with_proxy.call_count == 4


def test_get_number_of_portions_failure(mock_ask_gpt_with_proxy):
    # Настройка мока для постоянных некорректных ответов
    mock_ask_gpt_with_proxy.side_effect = ["invalid", "0", "-1", "NaN", "None"]

    user_message = "Борщ"
    with pytest.raises(ValueError, match="Не удалось определить количество порций после нескольких попыток."):
        get_number_of_portions(user_message)
    assert mock_ask_gpt_with_proxy.call_count == 5


# Тест функции get_ingredients_per_portion
def test_get_ingredients_per_portion_success(mock_ask_gpt_with_proxy):
    # Настройка мока для корректного JSON-ответа
    mock_response = json.dumps({
        "борщ": {
            "картофель": [200, "г"],
            "лук репчатый": [100, "г"],
            "свекла": [150, "г"]
        }
    })
    mock_ask_gpt_with_proxy.return_value = mock_response

    user_message = "Борщ на 4 порции"
    result = get_ingredients_per_portion(user_message)

    assert result == {
        "dish": "борщ",
        "ingredients": {
            "картофель": [200, "г"],
            "лук репчатый": [100, "г"],
            "свекла": [150, "г"]
        }
    }
    mock_ask_gpt_with_proxy.assert_called()


def test_get_ingredients_per_portion_invalid_json(mock_ask_gpt_with_proxy):
    # Настройка мока для некорректного JSON-ответа
    mock_ask_gpt_with_proxy.side_effect = [
        "Некорректный JSON",
        json.dumps({
            "борщ": {
                "картофель": [200, "г"],
                "лук репчатый": [100, "г"],
                "свекла": [150, "г"]
            }
        })
    ]

    user_message = "Борщ на 4 порции"
    result = get_ingredients_per_portion(user_message)

    assert result == {
        "dish": "борщ",
        "ingredients": {
            "картофель": [200, "г"],
            "лук репчатый": [100, "г"],
            "свекла": [150, "г"]
        }
    }
    assert mock_ask_gpt_with_proxy.call_count == 2


def test_get_ingredients_per_portion_failure(mock_ask_gpt_with_proxy):
    # Настройка мока для постоянных некорректных ответов
    mock_ask_gpt_with_proxy.side_effect = ["invalid", "{}", "{invalid_json}", "[]", "null"]

    user_message = "Борщ на 4 порции"
    with pytest.raises(ValueError, match="Не удалось получить корректный JSON после нескольких попыток."):
        get_ingredients_per_portion(user_message)
    assert mock_ask_gpt_with_proxy.call_count == 5


# Тест функции get_ingredients_list
def test_get_ingredients_list_success(mock_ask_gpt_with_proxy):
    # Настройка мока для функций get_number_of_portions и get_ingredients_per_portion
    # Предполагаем, что вызов ask_gpt_with_proxy сначала для get_number_of_portions, затем для get_ingredients_per_portion
    mock_ask_gpt_with_proxy.side_effect = ["4", json.dumps({
        "борщ": {
            "картофель": [200, "г"],
            "лук репчатый": [100, "г"],
            "свекла": [150, "г"]
        }
    })]

    user_message = "Борщ на 4 порции"
    result = get_ingredients_list(user_message)

    assert result == {
        "dish": "борщ",
        "ingredients": {
            "картофель": [800, "г"],  # 200 * 4
            "лук репчатый": [400, "г"],  # 100 * 4
            "свекла": [600, "г"]  # 150 * 4
        }
    }
    assert mock_ask_gpt_with_proxy.call_count == 2


def test_get_ingredients_list_failure_in_portions(mock_ask_gpt_with_proxy):
    # Настройка мока для get_number_of_portions, чтобы вызвать ошибку
    mock_ask_gpt_with_proxy.side_effect = ["invalid", "0", "-1", "NaN", "None"]

    user_message = "Борщ на 4 порции"
    result = get_ingredients_list(user_message)

    assert "error" in result
    assert result["error"] == "Не удалось определить количество порций после нескольких попыток."
    assert mock_ask_gpt_with_proxy.call_count == 5


def test_get_ingredients_list_failure_in_ingredients(mock_ask_gpt_with_proxy):
    # Настройка мока: правильный portions, некорректные ingredients
    mock_ask_gpt_with_proxy.side_effect = [
        "4",
        "Некорректный JSON",
        json.dumps({
            "борщ": {
                "картофель": [200, "г"],
                "лук репчатый": [100, "г"],
                "свекла": [150, "г"]
            }
        })
    ]

    user_message = "Борщ на 4 порции"
    result = get_ingredients_list(user_message)

    assert result == {
        "dish": "борщ",
        "ingredients": {
            "картофель": [800, "г"],  # 200 * 4
            "лук репчатый": [400, "г"],  # 100 * 4
            "свекла": [600, "г"]  # 150 * 4
        }
    }
    assert mock_ask_gpt_with_proxy.call_count == 3


# Тест функции get_preparation_instructions
def test_get_preparation_instructions_success(mock_ask_gpt_with_proxy):
    # Настройка мока для успешного ответа
    mock_ask_gpt_with_proxy.return_value = "1. Нарежьте картофель.\n2. Варите свеклу."

    dish = "борщ"
    ingredients = {
        "картофель": [800, "г"],
        "лук репчатый": [400, "г"],
        "свекла": [600, "г"]
    }

    instructions = get_preparation_instructions(dish, ingredients)

    assert instructions == "1. Нарежьте картофель.\n2. Варите свеклу."
    mock_ask_gpt_with_proxy.assert_called()


def test_get_preparation_instructions_empty_response(mock_ask_gpt_with_proxy):
    # Настройка мока для пустого ответа, затем успешного
    mock_ask_gpt_with_proxy.side_effect = ["", "1. Нарежьте картофель.\n2. Варите свеклу."]

    dish = "борщ"
    ingredients = {
        "картофель": [800, "г"],
        "лук репчатый": [400, "г"],
        "свекла": [600, "г"]
    }

    instructions = get_preparation_instructions(dish, ingredients)

    assert instructions == "1. Нарежьте картофель.\n2. Варите свеклу."
    assert mock_ask_gpt_with_proxy.call_count == 2


def test_get_preparation_instructions_failure(mock_ask_gpt_with_proxy):
    # Настройка мока для постоянных ошибок
    mock_ask_gpt_with_proxy.side_effect = Exception("API Error")

    dish = "борщ"
    ingredients = {
        "картофель": [800, "г"],
        "лук репчатый": [400, "г"],
        "свекла": [600, "г"]
    }

    with pytest.raises(ValueError, match="Не удалось получить инструкцию по приготовлению после нескольких попыток."):
        get_preparation_instructions(dish, ingredients)
    assert mock_ask_gpt_with_proxy.call_count == 5


# Дополнительные тесты для проверки интеграции
def test_full_flow_success(mock_ask_gpt_with_proxy):
    # Настройка мока для последовательных вызовов:
    # 1. get_number_of_portions: "4"
    # 2. get_ingredients_per_portion: корректный JSON
    # 3. get_preparation_instructions: корректные инструкции
    mock_ask_gpt_with_proxy.side_effect = [
        "4",
        json.dumps({
            "борщ": {
                "картофель": [200, "г"],
                "лук репчатый": [100, "г"],
                "свекла": [150, "г"]
            }
        }),
        "1. Нарежьте картофель.\n2. Варите свеклу."
    ]

    user_message = "Борщ на 4 порции"
    ingredients_list = get_ingredients_list(user_message)

    assert ingredients_list == {
        "dish": "борщ",
        "ingredients": {
            "картофель": [800, "г"],  # 200 * 4
            "лук репчатый": [400, "г"],  # 100 * 4
            "свекла": [600, "г"]  # 150 * 4
        }
    }
    assert mock_ask_gpt_with_proxy.call_count == 2

    # Получение инструкций
    instructions = get_preparation_instructions(ingredients_list["dish"], ingredients_list["ingredients"])
    assert instructions == "1. Нарежьте картофель.\n2. Варите свеклу."
    assert mock_ask_gpt_with_proxy.call_count == 3