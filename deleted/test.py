from bs4 import BeautifulSoup, NavigableString
import requests
import re
from test2 import get_property_urls 

BASE_URL = "https://www.bezrealitky.cz/nemovitosti-byty-domy/591711-nabidka-pronajem-bytu-moravanska-praha"

# Заголовки для имитации браузера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

response = requests.get(BASE_URL, headers=HEADERS)
soup = BeautifulSoup(response.text, "html.parser")

def clean_string(string):
    cleaned = re.sub(r'\b\d+[.,\d\s]*\s?m²', '', string) #debugged 1 200 m2
    return cleaned

def find_extra_info(soup_element):

    extra_info = {}
    extra_info_to_scrap = ('Balkón', 'Bezbariérový přístup', 'Parkování', 'Výtah', 'Garáž', 'Sklep', 'Lodžie', 'Terasa', 'Předzahrádka')
    
    tables = soup_element.find_all("table")
    
    for i in range(2, 4):


        rows = tables[i].find_all("td")
        for row in rows:
            if row and row.string:

                cleaned_string = clean_string(row.string).strip()
                print(cleaned_string, "-", cleaned_string in extra_info_to_scrap)

                if cleaned_string in extra_info_to_scrap:
                    key = cleaned_string
                    value = True
                    extra_info[key] = value

    return extra_info



print(find_extra_info(soup))