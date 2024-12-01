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
def parse_products(category_url):
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
                name = name_element.get('title').strip().encode('utf-8').decode('unicode_escape')
                link = BASE_URL + name_element['href']
            quantity = card.select_one('.ProductCard__weight')
            if quantity:
                quantity = quantity.get_text(strip=True)
            price = card.select_one('.Price.Price--md.Price--gray.Price--label')
            if price:
                price = price.get_text(strip=True).encode('utf-8').decode('unicode_escape')

            # Добавляем информацию о продукте в список
            products.append({
                "name": name,
                "link": link,
                "quantity": quantity,
                "price": price
            })

    return products


# Основная функция для парсинга всех категорий и записи в JSON
def parse_product_from_vv():
    categories = get_categories()
    data = {}

    for category in categories[5:]:
        print(f"Парсим категорию: {category['name']}", end='... ')
        try:
            products = parse_products(category["url"])
            data[category['name']] = products
            print(f"обработано {len(products)} продуктов")
        except:
            print("Не получилось обработать")

    with open(BD_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Все продукты сохранены во {BD_path}")


def calculate_packs_needed(quantity_needed, unit_needed, pack_quantity, pack_unit):
    # Словарь для конверсии единиц измерения
    unit_conversion = {
        "г": 1,         # граммы
        "кг": 1000,     # килограммы
        "мл": 1,        # миллилитры
        "л": 1000,      # литры
        "шт": 1         # штуки
    }

    # Проверяем, есть ли такие единицы измерения в словаре
    if unit_needed not in unit_conversion or pack_unit not in unit_conversion:
        return -1  # Не удалось сопоставить

    # Приводим оба значения к единой базовой единице (например, граммы или миллилитры)
    base_needed = quantity_needed * unit_conversion[unit_needed]
    base_pack = pack_quantity * unit_conversion[pack_unit]

    # Проверяем, возможно ли использование упаковки
    if base_pack == 0 or base_needed == 0:
        return -1  # Невозможно сопоставить

    # Считаем количество упаковок
    packs_needed = base_needed / base_pack

    # Возвращаем количество упаковок, округлённое вверх до целого числа
    return int(packs_needed) if packs_needed.is_integer() else int(packs_needed) + 1


def get_links_from_list(products_needed, json_file):
    """
    Функция для поиска продуктов из словаря в JSON-файле базы данных.

    :param products_needed: Словарь с нужными продуктами и их количеством/единицами измерения.
    :param json_file: Имя JSON-файла с базой данных продуктов.
    :return: Словарь с категориями и списками найденных продуктов.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        database = json.load(f)

    result = []

    # Перебираем категории в базе данных
    for category, products in database.items():
        for product in products:
            product_name = product.get("name", "").lower()

            # Проверяем, содержится ли продукт в списке нужных
            for needed_product, details in products_needed.items():
                needed_name = needed_product.lower()
                needed_quantity = details[0]  # Необходимое количество
                needed_unit = details[1]  # Единица измерения

                if all(word in product_name.split() for word in needed_name.split()):
                    try:
                        product_price = 0
                        for i in product.get("price", ""):
                            if i.isnumeric():
                                product_price = product_price * 10 + int(i)
                            else:
                                break
                    except:
                        product_price = 1e9

                    try:
                        product_quantity = int(product["quantity"].split()[0])
                        product_unit = product["quantity"].split()[1]
                    except:
                        continue

                    # Расчёт необходимого количества упаковок
                    packs_needed = calculate_packs_needed(needed_quantity, needed_unit, product_quantity, product_unit)

                    if packs_needed == -1:
                        continue

                    # Общая стоимость для текущего продукта
                    total_price = product_price * packs_needed

                    # Оптимизация: выбираем продукт с минимальной общей стоимостью
                    existing_product = next((p for p in result if needed_name in p["name"].lower()), None)
                    if not existing_product or total_price < existing_product.get("total_price", float('inf')):
                        if existing_product:
                            result[category].remove(existing_product)
                        result.append({
                            **product,
                            "packs_needed": packs_needed,
                            "total_price": total_price
                        })
                    del products_needed[needed_product]
                    break

    return result
parse_product_from_vv()

products_list = {
    'свекла': [2100, 'г'],
    'капуста': [1400, 'г'],
    'картофель': [1400, 'г'],
    'морковь': [700, 'г'],
    'лук репчатый': [700, 'г'],
    'томатная паста': [420, 'г'],
    'говядина': [2100, 'г'],
    'вода': [7000, 'мл'],
    'соль': [70, 'г'],
    'сахар': [70, 'г'],
    'уксус': [70, 'мл'],
    'лавровый лист': [14, 'шт'],
    'черный перец горошком': [28, 'г'],
    'чеснок': [70, 'г'],
    'растительное масло': [140, 'мл']
}


