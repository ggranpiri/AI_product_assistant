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
            products = parse_products(category["url"])
            data[category['name']] = products
            print(f"обработано {len(products)} продуктов")
        except:
            print("Не получилось обработать")

    with open(BD_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Все продукты сохранены во {BD_path}")

# parse_product_from_vv()
def convert_to_grams(quantity, unit):
    # Словарь для конверсии в граммы
    unit_conversion = {
        "г": 1,
        "кг": 1000,
        "мл": 1,  # Примерно, для воды 1 мл = 1 г
        "л": 1000,
        "шт": 1  # Если штуки нужно пересчитывать, добавьте дополнительную логику
    }
    # Проверка наличия единицы измерения
    if unit not in unit_conversion:
        return -1  # Неизвестная единица измерения
    return quantity * unit_conversion[unit]


def calculate_packs_needed(quantity_needed, unit_needed, pack_quantity, pack_unit):
    # Переводим нужное количество и количество в упаковке в граммы
    base_needed = convert_to_grams(quantity_needed, unit_needed)
    base_pack = convert_to_grams(pack_quantity, pack_unit)

    # Проверяем корректность преобразования
    if base_needed == -1 or base_pack == -1 or base_pack == 0:
        return -1  # Невозможно сопоставить

    # Считаем количество упаковок
    packs_needed = base_needed / base_pack

    # Возвращаем округлённое вверх значение
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

    result = [{} for _ in range(len(products_needed))]

    # Перебираем категории в базе данных
    for category, products in database.items():
        for product in products:
            product_name = product.get("name", "").lower()
            # Проверяем, содержится ли продукт в списке нужных
            for i, [needed_product, details] in enumerate(products_needed.items()):
                needed_name = needed_product.lower()
                needed_quantity = details[0]  # Необходимое количество
                needed_unit = details[1]  # Единица измерения

                if len(product_name.split()) - len(needed_name.split()) > 3:
                    continue

                if all(word in product_name.split() for word in needed_name.split()):
                    product_price = product["price"]

                    try:
                        if not product["quantity"]:
                            product["quantity"] = "1 кг"

                        product_quantity = int(product["quantity"].split()[0])
                        product_unit = product["quantity"].split()[1]
                    except:
                        continue

                    # Переводим количество продукта в граммы
                    product_weight_in_grams = convert_to_grams(product_quantity, product_unit)
                    if product_weight_in_grams == -1:
                        continue

                    # Стоимость за грамм
                    cost_per_gram = product_price / product_weight_in_grams

                    # Расчёт необходимого количества упаковок
                    packs_needed = calculate_packs_needed(needed_quantity, needed_unit, product_quantity, product_unit)
                    if packs_needed == -1:
                        continue

                    # Общая стоимость для текущего продукта
                    total_price = product_price * packs_needed

                    # Оптимизация: выбираем продукт с минимальной стоимостью за грамм

                    if not result[i] or cost_per_gram < result[i].get("cost_per_gram", float('inf')):
                        if result[i]:
                            result[i] = {}
                        result[i] = {
                            **product,
                            "packs_needed": packs_needed,
                            "total_price": total_price,
                            "cost_per_gram": cost_per_gram
                        }
                    break
    print(*result, sep='\n')
    return result


products_list = {
    'соль': [70, 'г'],
    'свекла': [2100, 'г'],
    'капуста': [1400, 'г'],
    'картофель': [1400, 'г'],
    'морковь': [700, 'г'],
    'лук репчатый': [700, 'г'],
    'томатная паста': [420, 'г'],
    'говядина': [2100, 'г'],
    'вода': [7000, 'мл'],
    'сахар': [70, 'г'],
    'уксус': [70, 'мл'],
    'лавровый лист': [14, 'шт'],
    'черный перец горошком': [28, 'г'],
    'чеснок': [70, 'г'],
    'растительное масло': [140, 'мл']
}

#get_links_from_list(products_list, "vkusvill_products.json")
