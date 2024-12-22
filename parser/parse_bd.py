import requests
from bs4 import BeautifulSoup
import json
import re

from config import BD_path

# Задаем User-Agent для имитации реального браузера
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

BASE_URL = "https://vkusvill.ru"


# Функция для получения ссылок на категории
def get_categories():
    response = requests.get(f"{BASE_URL}/goods/", headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    # Находим блоки с категориями по классу
    categories = []
    for link in soup.select(".VVCatalog2020Menu__List a"):
        categories.append({
            "name": link.get_text(strip=True),
            "url": BASE_URL + link["href"]
        })
    return categories


# Функция для получения количества страниц в категории
def get_total_pages(category_url):
    response = requests.get(category_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    # Ищем кнопку последней страницы
    last_page = soup.select(".VV_Pager.js-lk-pager a")
    if len(last_page) > 1:
        return int(last_page[-2].get("data-page"))
    else:
        return 1


# Функция для парсинга продуктов на странице категории
def parse_products_in_category(category_url):
    total_pages = get_total_pages(category_url)
    products = []

    # Проходим по каждой странице категории
    for page in range(1, total_pages + 1):
        page_url = f"{category_url}?PAGEN_1={page}"
        response = requests.get(page_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Парсим карточки товаров на странице
        product_cards = soup.select('.ProductCards__list .ProductCard')

        for card in product_cards:
            name_element = card.select_one('.ProductCard__link')
            link = ''
            if name_element:
                name = re.sub(r'[^a-zA-Z0-9а-яА-ЯёЁ]', ' ', name_element.get('title').strip())
                link = BASE_URL + name_element['href']
            quantity = card.select_one('.ProductCard__weight')
            if quantity:
                quantity = re.sub(r'[^a-zA-Z0-9а-яА-ЯёЁ]', ' ', quantity.get_text(strip=True))
            price = card.select_one('.Price.Price--md.Price--gray.Price--label')
            if price:
                price = int(re.sub(r'[^0-9]', '', price.get_text(strip=True)))

            # Добавляем информацию о продукте в список
            products.append({
                "name": name,
                "link": link,
                "quantity": quantity,
                "price": price
            })
    return products


# Основная функция для парсинга всех категорий и записи в JSON
good_category = {
    "Овощи, фрукты, ягоды, зелень",
    "Хлеб и выпечка",
    "Выпекаем сами",
    "Молочные продукты, яйцо",
    "Мясо, птица",
    "Рыба, икра и морепродукты",
    "Колбаса, сосиски, деликатесы",
    "Замороженные продукты",
    "Сыры",
    "Напитки",
    "Орехи, чипсы и снеки",
    "Вегетарианское и постное",
    "Крупы, макароны, мука",
    "Алкоголь",
    "Консервация",
    "Чай и кофе",
    "Масла, соусы, специи, сахар и соль"
}


def parse_product_from_vv():
    categories = get_categories()
    data = {}

    for category in categories:
        if category["name"] not in good_category:
            continue
        print(f"Парсим категорию: {category['name']}", end='... ')
        try:
            products = parse_products_in_category(category["url"])
            data[category['name']] = products
            print(f"обработано {len(products)} продуктов")
        except:
            print("Не получилось обработать")

    with open(BD_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Все продукты сохранены во {BD_path}")

parse_product_from_vv()