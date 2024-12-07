import unittest
from unittest.mock import patch, MagicMock
from parser.parse_bd import get_categories, get_total_pages, parse_product_from_vv


class TestGetCategories(unittest.TestCase):

    @patch('parser.parse_bd.requests.get')  # Патчим requests.get
    @patch('parser.parse_bd.BeautifulSoup')  # Патчим BeautifulSoup
    def test_get_categories(self, mock_soup, mock_get):
        # Мокируем ответ от requests.get
        mock_response = MagicMock()
        mock_response.text = '<html><body><div class="VVCatalog2020Menu__List"><a href="/category1">Category 1</a><a href="/category2">Category 2</a></div></body></html>'
        mock_get.return_value = mock_response

        # Мокируем BeautifulSoup
        mock_soup.return_value.select.return_value = [
            MagicMock(get_text=MagicMock(return_value='Category 1'), __getitem__=MagicMock(return_value='/category1')),
            MagicMock(get_text=MagicMock(return_value='Category 2'), __getitem__=MagicMock(return_value='/category2'))
        ]

        # Выполняем тестируемую функцию
        categories = get_categories()

        # Проверяем, что функция вернула правильный список категорий
        self.assertEqual(categories, [
            {"name": "Category 1", "url": "https://vkusvill.ru/category1"},
            {"name": "Category 2", "url": "https://vkusvill.ru/category2"}
        ])


class TestGetCategories(unittest.TestCase):

    @patch('parser.parse_bd.requests.get')  # Патчим requests.get
    @patch('parser.parse_bd.BeautifulSoup')  # Патчим BeautifulSoup
    def test_get_categories(self, mock_soup, mock_get):
        # Мокируем ответ от requests.get
        mock_response = MagicMock()
        mock_response.text = '<html><body><div class="VVCatalog2020Menu__List"><a href="/category1">Category 1</a><a href="/category2">Category 2</a></div></body></html>'
        mock_get.return_value = mock_response

        # Мокируем BeautifulSoup
        mock_soup.return_value.select.return_value = [
            MagicMock(get_text=MagicMock(return_value='Category 1'), __getitem__=MagicMock(return_value='/category1')),
            MagicMock(get_text=MagicMock(return_value='Category 2'), __getitem__=MagicMock(return_value='/category2'))
        ]

        # Выполняем тестируемую функцию
        categories = get_categories()

        # Проверяем, что функция вернула правильный список категорий
        self.assertEqual(categories, [
            {"name": "Category 1", "url": "https://vkusvill.ru/category1"},
            {"name": "Category 2", "url": "https://vkusvill.ru/category2"}
        ])


class TestGetTotalPages(unittest.TestCase):

    @patch('parser.parse_bd.requests.get')  # Патчим requests.get
    @patch('parser.parse_bd.BeautifulSoup')  # Патчим BeautifulSoup
    def test_get_total_pages_multiple(self, mock_soup, mock_get):
        # Мокируем ответ от requests.get
        mock_response = MagicMock()
        mock_response.text = '<html><body><div class="VV_Pager js-lk-pager"><a data-page="1">1</a><a data-page="2">2</a><a data-page="3">3</a></div></body></html>'
        mock_get.return_value = mock_response

        # Мокируем BeautifulSoup
        mock_soup.return_value.select.return_value = [
            MagicMock(get=MagicMock(return_value="1")),
            MagicMock(get=MagicMock(return_value="2")),
            MagicMock(get=MagicMock(return_value="3"))
        ]

        # Тестируем функцию
        total_pages = get_total_pages("https://vkusvill.ru/category")

        # Проверяем, что функция вернула правильное количество страниц
        self.assertEqual(total_pages, 2)

    @patch('parser.parse_bd.requests.get')  # Патчим requests.get
    @patch('parser.parse_bd.BeautifulSoup')  # Патчим BeautifulSoup
    def test_get_total_pages_single(self, mock_soup, mock_get):
        # Мокируем ответ от requests.get (только одна страница)
        mock_response = MagicMock()
        mock_response.text = '<html><body><div class="VV_Pager js-lk-pager"><a data-page="1">1</a></div></body></html>'
        mock_get.return_value = mock_response

        # Мокируем BeautifulSoup
        mock_soup.return_value.select.return_value = [
            MagicMock(get=MagicMock(return_value="1"))
        ]

        # Тестируем функцию
        total_pages = get_total_pages("https://vkusvill.ru/category")

        # Проверяем, что функция вернула 1 страницу
        self.assertEqual(total_pages, 1)

    @patch('parser.parse_bd.requests.get')  # Патчим requests.get
    @patch('parser.parse_bd.BeautifulSoup')  # Патчим BeautifulSoup
    def test_get_total_pages_no_pages(self, mock_soup, mock_get):
        # Мокируем ответ от requests.get (нет страниц)
        mock_response = MagicMock()
        mock_response.text = '<html><body><div class="VV_Pager js-lk-pager"></div></body></html>'
        mock_get.return_value = mock_response

        # Мокируем BeautifulSoup
        mock_soup.return_value.select.return_value = []

        # Тестируем функцию
        total_pages = get_total_pages("https://vkusvill.ru/category")

        # Проверяем, что функция вернула 1 страницу, если не найдено страниц
        self.assertEqual(total_pages, 1)


class TestParseProductFromVV(unittest.TestCase):
    @patch("parser.parse_bd.parse_products_in_category")
    @patch("parser.parse_bd.get_categories")
    def test_parse_product_from_vv(self, mock_get_categories, mock_parse_products):
        # Настройка тестовых данных
        mock_get_categories.return_value = [
            {"name": "Напитки", "url": "https://example.com/Напитки"}
        ]
        mock_parse_products.return_value = [
            {"name": "Product1", "price": 100, "quantity": "500 г"}
        ]

        # Глобальные переменные
        global good_category, BD_path
        good_category = ["Напитки"]
        BD_path = "test_db.json"

        # Вызов тестируемой функции
        parse_product_from_vv()

        # Проверяем, что get_categories был вызван
        mock_get_categories.assert_called_once()

        # Проверяем, что parse_products_in_category был вызван с правильным аргументом
        mock_parse_products.assert_called_once_with("https://example.com/Напитки")
