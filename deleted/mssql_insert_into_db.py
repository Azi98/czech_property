"""
Открывает JSON файлик с готовыми для отправку в базу данных объявлениями и отправляет их 
"""

import pyodbc
import json

SERVER = 'property09.database.windows.net'
DATABASE = 'property_db'
USERNAME = 'azna09'
PASSWORD = 'BedaStudentSeptember2024!'

connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'

conn = pyodbc.connect(connectionString) 
cursor = conn.cursor()

field_mapping = {
    "Cena": "Price",
    "Poplatky za služby": "ServiceFees",
    "Poplatky za energie": "EnergyFees",
    "Vratná kauce": "RefundableDeposit",
    "Administrativní poplatek": "AdministrativeFee",
    "Číslo inzerátu": "ListingID",

    "Dispozice": "Layout",
    "Vybaveno": "Furnished",
    "Stav": "P_condition",
    "Konstrukce budovy": "BuildingType",
    "Vlastnictví": "P_Ownership",
    "PENB": "EnergyEfficiency",
    "Rekonstrukce": "Renovation",
    "Provedení": "Execution",
    "Stáří": "BuildingAge",
    "Užitná plocha": "UsableArea",
    "Umístění": "P_Location",
    "Dostupné od": "AvailableFrom",
    "Podlaží": "Floor",
    "Počet_Podlaží": "TotalFloors",
    "Cena za jednotku": "PricePerUnit",
    "Vytápění": "Heating",

    "Balkón": "Balcony",
    "Výtah": "Elevator",
    "Lodžie": "Loggia",
    "Parkování": "Parking",
    "Garáž": "Garage",
    "Bezbariérový přístup": "BarrierFreeAccess",
    "Sklep": "Cellar",
    "Terasa": "Terrace",
    "Předzahrádka": "FrontGarden",

    "Ulice": "Street",
    "Město": "City",
    "Městská část": "District",
    "Kraj": "Region"
}

# Предположим, что ваш JSON-файл называется properties.json
with open("cleaned_properties.json", "r", encoding="utf-8") as f:
    data = json.load(f)  # data — это список объектов

# Для каждой записи в JSON... 
for item in data:
    # Сформируем словарь "колонка_в_БД" : "значение"
    row_dict = {}
    for json_key, db_col in field_mapping.items():
        val = item.get(json_key, None)

        if isinstance(val, bool):
            val = 1 if val else 0

        row_dict[db_col] = val

    # Важно проверить наличие обязательных полей: ListingID, Price
    if not row_dict.get("ListingID"):
        print(f"Пропускаем запись без ListingID: {item}")
        continue
    if row_dict.get("Price") is None:
        print(f"Пропускаем запись без цены (Price): {item}")
        continue

    # Соберём SQL-выражение INSERT
    columns = ", ".join(row_dict.keys())                # перечислим все колонки
    placeholders = ", ".join(["?"] * len(row_dict))     # под каждый столбец знак '?'
    values = list(row_dict.values())                    # значения в том же порядке

    sql = f"INSERT INTO [dbo].[Properties] ({columns}) VALUES ({placeholders})"

    # Выполняем INSERT.
    # Если нужно, можно обрабатывать исключения (например, при дублях ListingID).
    try:
        cursor.execute(sql, values)
    except pyodbc.IntegrityError as e:
        print(f"Ошибка при вставке записи {row_dict}. Возможно, дубль ListingID.")
        print(e)
        continue

# Зафиксируем изменения в БД
conn.commit()

# Закрываем курсор и соединение
cursor.close()
conn.close()

print("Загрузка завершена.")

#1) юзер вводит запрос в интерфейсе - получение промпта тригерит функцию create_sql_request и передает в нее промпт пользователя 
#2) функция create_sql_request возвращает sql код, который затем передается другой функции (do_sql_request), которая подключается к ДБ и выполняет этот SQL запрос
#3) do_sql_request возврашает результат SQL запроса