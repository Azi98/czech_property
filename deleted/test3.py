from bs4 import BeautifulSoup
import requests
import re

LIST_URL = "https://www.bezrealitky.cz/nemovitosti-byty-domy/804560-nabidka-pronajem-bytu-bratislavska-brno"

# Заголовки для имитации браузера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

response = requests.get(LIST_URL, headers=HEADERS)
soup = BeautifulSoup(response.text, "html.parser")

def find_address_info(soup_element):
    """
    Ищет в soup_element адрес и возвращает его в виде словаря:
    {
        "street": str,
        "city": str,
        "district": str или None,
        "region": str
    }
    Если в адресе не указан край (например, для Праги),
    то в 'region' подставляется значение города.
    """
    address_span = soup_element.find("h1", class_="mb-3 mb-lg-10 h2").find("span", class_="d-block text-perex-lg text-grey-dark")

    if not address_span:
        # Если элемент не найден, можно вернуть None или пустой словарь
        return {
            "street": None,
            "city": None,
            "district": None,
            "region": None
        }

    full_address = address_span.get_text(strip=True)
    # Пример строки: "Bratislavská, Brno - Zábrdovice, Jihomoravský kraj"
    # Или для Праги: "Vinohradská, Praha - Vinohrady"

    # Делим строку по запятым
    parts = [p.strip() for p in full_address.split(",")]

    # Предположим, что parts[0] = улица
    street = parts[0] if len(parts) > 0 else None

    # Предположим, что parts[1] = "Brno - Zábrdovice" или "Praha - Vinohrady" (город и район)
    # или просто "Praha" (если нет района)
    city = None
    district = None
    region = None

    if len(parts) > 1:
        # Попробуем отделить город от района
        city_district_part = parts[1]
        dash_parts = [dp.strip() for dp in city_district_part.split("-")]

        if len(dash_parts) == 2:
            # Например "Brno" и "Zábrdovice"
            city = dash_parts[0]
            district = dash_parts[1]
        else:
            # Если нет дефиса, значит весь кусок - это city, а district отсутствует
            city = city_district_part

    # Если есть третий элемент, предполагаем, что это край
    # Например "Jihomoravský kraj"
    if len(parts) > 2:
        region = parts[2]
    else:
        # Если края нет, но это Прага, подставляем в 'region' то же, что и в city
        # Часто в Праге адрес выглядит как: "Nějaká ulice, Praha - Žižkov"
        # без отдельного края
        if city and city.lower().startswith("praha"):
            region = city
        else:
            # Для других случаев (вдруг адрес обрезан), пусть region остаётся None
            region = None

    return {
        "street": street,
        "city": city,
        "district": district,
        "region": region
    }

print(find_address_info(soup))
#следующие шаги: 1) написать функционал для вытягивания остальной информации о недвижимости 
#1.1) нормализовать получаемую информацию 
#2) Написать функкионал для вытягивания инфо со всех страниц
#3) На этом этапе можно будет начать изучение того, как эти данные сохранять/структурировать/подготпаливать к отправке в базу данных


def save_to_json(file_path, new_data):
    # Если файл уже существует, загружаем существующие данные
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    # Объединяем новые данные с существующими
    updated_data = existing_data + new_data

    # Сохраняем обновлённые данные в файл
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)