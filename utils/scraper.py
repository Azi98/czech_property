"""do_scrape_bezrealitky это главная функция этого модуля. Она берет на вход BASE_URL (первую страницу с объявлениями), 
HEADERS (чтобы имитировать реального пользователя) и file_path - куда сохранит информацию о недвижимостях. Скрипт заходит на BASE_URL
вытягивает оттуда 15 urls объявлений, вытягивает из этих объявлений информацию о каждом, затем переходит на следующую странцу и так 
до страницы, которую мы укажем (функционала, который сам узнает последнюю страницу пока что нет). Все вытянутые информации
о объявлениях он сохраняет в переменную, в виде словаря (для всех страниц которые мы укажем). Как только закончит проходить по страницам
он сохранит словарь из переменной в файлик json, название и путь к которому мы передаем в file_path.

Небольшой недочет то, что все объявления сначала сохраняются в переменную all_properties_data, что является напрягом для оперативки 
надо бы разбить на кусочки, но это уже мелочи.

Иными словами - это скрипт для полного вытягивания всех объявлений и информации о них и сохранения этих данных в JSON файлик. 
"""

from bs4 import BeautifulSoup # type: ignore
import requests
import re
import json
import extract_info

def get_num_of_pages(soup_object):
    last_page_number = soup_object.find_all('a', class_='page-link')[-2].text.strip()
    return int(last_page_number)

def get_property_urls(base_url):

    """
    Получение списка ссылок на объявления.
    """

    try:
        response = requests.get(base_url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Ошибка: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        links = [elem["href"] for elem in soup.find_all(href=re.compile("nemovitosti-byty-domy"))]
        
        return links
    
    except Exception as e:
        print(f"Ошибка при получении списка объявлений: {e}")
        return []

def do_scrape_bezrealitky(base_url, headers, file_path):

    """ 
    Основная функция.
    """
    
    try:

        all_properties_data = []  # Здесь будем хранить все объявления (словарики)
        count = 0

        for i in range(1, 3): #укажи в range количество страниц, по которым хочешь пройтись; i будет вставляться в адресную строку, чтобы достать из нее все адреса объявлений для скрапинга

            url_with_i_page = re.sub(r'(?<=page=)\d+', str(i), base_url) #вставляет в url страницу i (чтобы на нее переходить при новых итерациях)
            urls = get_property_urls(url_with_i_page)


            if not urls:
                print("Список ссылок пуст. Программа завершена.")
                return

            for j, url in enumerate(urls, 1):

                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, "html.parser")

                property_info = extract_info.get_property_info(soup)
                if property_info:
                    print(f"Достаю информацию о недвижимости {j}, Страница {i}")
                    all_properties_data.append(property_info)
                    count += 1
                else:
                    print(f"Не удалось получить данные для {url}")
                
                
            
            print(f"Пока собрано {count} объявлений")
            

        with open(file_path, "w", encoding="utf-8") as f:
                json.dump(all_properties_data, f, ensure_ascii=False, indent=4)
        print(f"Сохранено {len(all_properties_data)} объявлений здесь {file_path}")
    
    except Exception as e:
        print(f"Ошибка при выполнении программы: {e}")

BASE_URL = "https://www.bezrealitky.cz/vyhledat?offerType=PRONAJEM&estateType=BYT&location=fromMap&country=ceska-republika&currency=CZK&page=1&regionOsmIds=R51684&osm_value=%C4%8Cesko"

HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

file_path = "../data/uncleaned_data_check.json"


if __name__ == "__main__":
    do_scrape_bezrealitky(BASE_URL, HEADERS, file_path)



