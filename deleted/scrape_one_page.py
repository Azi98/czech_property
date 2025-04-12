"""Передаем в главную функцию .soup страницу. Скрипт достанет всю информацию из объявления и вернет в виде словаря
Проще говоря, передаем объявление, получаем словарик со всеми данными этого объявления"""

from bs4 import BeautifulSoup
import re
import requests

#Тут вытягивается цена объявления и возвращается в виде словаря 
def find_price_and_bills(soup_object):
    found_prices = {}

    prices_container = soup_object.find("div", class_="mb-lg-9 mb-6")

    main_price = prices_container.find("strong", class_="h4 fw-bold").get_text(strip=True)

    found_prices["Cena"] = main_price
    
    bills_lst = soup_object.find_all("div", class_="justify-content-between mb-2 mb-last-0 row")

    for bill in bills_lst:
        span_elems = bill.find_all("span", class_="col-auto")

        # Обычно span_elems[0] — это колонка с названием («+ Poplatky…», «+ Vratná kauce»),
        # а span_elems[1] — это колонка с ценой («1 500 Kč» и т.д.).
        if len(span_elems) == 2:

            service_name = span_elems[0].get_text(strip=True)
            service_price = span_elems[1].get_text(strip=True)

            # Убираем ведущий плюс и пробел, если он есть
            service_name = service_name.replace("+ ", "")

            found_prices[service_name] = service_price

    return found_prices

#Тут вытягивается адрес недвжимости и возвращается в виде словаря 
def find_address_info(soup_object):
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
    address_span = soup_object.find("h1", class_="mb-3 mb-lg-10 h2").find("span", class_="d-block text-perex-lg text-grey-dark")
    if not address_span:
        # Если элемент не найден, можно вернуть None или пустой словарь
        return {
            "Ulice": None,
            "Město": None,
            "Městská část": None,
            "Kraj": None
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
        "Ulice": street,
        "Město": city,
        "Městská část": district,
        "Kraj": region
    }

#Тут вытягивается информация с таблицы Parametry nemovitosti и возвращается в виде словаря 
def find_main_info(soup_object):

    main_info = {}

    tables = soup_object.find_all("table")
    for i in range(2):
        rows = tables[i].find_all("tr")
        for row in rows:
            key = row.find("th").get_text(strip=True)
            value = row.find("td").get_text(strip=True)

            main_info[key] = value
    
    return main_info

#Тут вытягивается информация с таблицы Co tato nemovitost nabízí? и возвращается в виде словаря 
def find_extra_info(soup_object):

    extra_info = {}
    extra_info_to_scrap = ('Balkón', 'Bezbariérový přístup', 'Parkování', 'Výtah', 'Garáž', 'Sklep', 'Lodžie', 'Terasa', 'Předzahrádka')
    
    tables = soup_object.find_all("table")
    
    for i in range(2, 4):


        rows = tables[i].find_all("td")
        for row in rows:
            if row and row.string:

                cleaned_string = re.sub(r'\b\d+[.,\d\s]*\s?m²', '', row.string).strip() #re для очистки строки (Убираем размеры, указанные в формате (например, "3 m²", "2,5 m²"))

                if cleaned_string in extra_info_to_scrap:
                    key = cleaned_string
                    value = True
                    extra_info[key] = value
    
    return extra_info

#Это главная функция, которая возвращает всю информацию об объявлении в виде словаря
def get_property_info(soup_object): 
    
    """
    Получение информации для одного конкретного объявления.
    """

    try:

        prices_bills_dict = find_price_and_bills(soup_object)
        main_info_dict = find_main_info(soup_object)
        extra_info_dict = find_extra_info(soup_object)
        address_dict = find_address_info(soup_object)

        property_info_dict = {
            **prices_bills_dict,
            **main_info_dict,
            **extra_info_dict,
            **address_dict
        }       
        
        return property_info_dict

    except Exception as e:
        print(f"Ошибка при обработке страницы: {e}")
        return None
    
def get_num_of_pages(soup_object):
    last_page_number = soup_object.find_all('a', class_='page-link')[-2].text.strip()
    return int(last_page_number)
    
if __name__ == "__main__":

    #url с объявлением
    URL = "https://www.bezrealitky.cz/vyhledat?offerType=PRONAJEM&estateType=BYT&osm_value=Česko&regionOsmIds=R51684&currency=CZK&country=ceska-republika"

    # Заголовки для имитации браузера
    HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(URL, headers=HEADERS)

        if response.status_code != 200:
            print(f"Ошибка при запросе {URL}: {response.status_code}")
            
        soup = BeautifulSoup(response.text, "html.parser")

        print(get_num_of_pages(soup))


    except Exception as e:
        print(f"Ошибка при обработке страницы: {e}")