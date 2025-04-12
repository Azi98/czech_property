from bs4 import BeautifulSoup
import requests
import re


LIST_URL = "https://www.bezrealitky.cz/nemovitosti-byty-domy/876171-nabidka-pronajem-bytu-tyrsova-kutna-hora"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
#Передаем soup. элемент со страницей объявления как параметр
 
def find_price_and_bills(soup_element):
    found_prices = {}

    prices_container = soup_element.find("div", class_="mb-lg-9 mb-6")

    main_price = prices_container.find("strong", class_="h4 fw-bold").get_text(strip=True)

    found_prices["Cena"] = main_price
    
    bills_lst = soup_element.find_all("div", class_="justify-content-between mb-2 mb-last-0 row")

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

try:
    response = requests.get(LIST_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    price_element = soup.find("strong", class_="h4 fw-bold")

    find_price_and_bills(soup)


except Exception as e:
    print(f"Ошибка при получении списка объявлений: {e}")

