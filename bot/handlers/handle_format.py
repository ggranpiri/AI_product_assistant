def format_ingredients_list(ingredients, ingredients_list_with_links):
    """Форматирование списка ингредиентов."""
    total_price = 0
    formatted_list = ""

    for i, key in enumerate(ingredients.keys()):
        item = ingredients_list_with_links[i] if i < len(ingredients_list_with_links) else None
        if item:
            name, link, packs_needed, price = item.get('name', 'неизвестно'), item.get('link', '#'), item.get(
                'packs_needed', 'неизвестно'), item.get('price', 0)
            formatted_list += f"{i + 1}. [{name}]({link}) - {packs_needed} шт, {price} ₽\n"
            total_price += price
        else:
            formatted_list += f"{i + 1}. {key} - не удалось найти\n"

    return total_price, formatted_list


def format_recipe_ingredients(ingredients, ingredients_list_with_links):
    """Форматирование списка ингредиентов для рецепта."""
    formatted_list = "*Ваш список продуктов для рецепта:*\n\n"
    for i, (ingredient, _) in enumerate(ingredients.items()):
        item = ingredients_list_with_links[i] if i < len(ingredients_list_with_links) else None
        if item:
            name, link, packs_needed, price = item.get('name', 'неизвестно'), item.get('link', '#'), item.get(
                'packs_needed', 'неизвестно'), item.get('price', 'неизвестно')
            formatted_list += f"{i + 1}. [{name}]({link}) - {packs_needed} шт, {price} ₽\n"
        else:
            formatted_list += f"{i + 1}. {ingredient} - не найдено\n"
    return formatted_list