"""Этот скрипт нужен для того, чтобы загрузить очищенные данные (и уникальные), полученные со скрапинга, 
в нашу базу данных"""


import psycopg2
from psycopg2 import sql
import json

# Настройки подключения к базе данных
DB_SETTINGS = {
    "dbname": "property_project",
    "user": "postgres",
    "password": "250998",
    "host": "localhost",
    "port": 5432
}

field_mapping = {
    "Cena": "Price",
    "Poplatky za služby": "ServiceFees",
    "Poplatky za energie": "EnergyFees",
    "Administrativní poplatek": "AdministrativeFee",
    "Vratná kauce": "RefundableDeposit",
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

columns_db = [column_name for column_name in field_mapping.keys()]

# Предположим, что ваш JSON-файл называется properties.json
with open("../data/cleaned_properties_unique.json", "r", encoding="utf-8") as f:
    data = json.load(f)  # data — это список объектов

lst_of_dict = []

for item in data:

    new_lst = list()

    for column in columns_db:
        if column in list(item.keys()):
             new_lst.append(item[column])
        elif column not in list(item.keys()):
            new_lst.append(None)
    
    lst_of_dict.append(dict(zip(list(field_mapping.values()), new_lst)))
 

values = []

for item in lst_of_dict:
    values.append(tuple(item.values()))


placeholders = ", ".join(["%s"] * len(columns_db)) 
sql_columns = ', '.join(list(field_mapping.values()))
sql_values = values
sql_table_name = "Properties"

sql_query = f"""
INSERT INTO {sql_table_name} ({sql_columns})
VALUES ({placeholders})
"""

# Подключение к базе данных
try:
    conn = psycopg2.connect(**DB_SETTINGS)
    cursor = conn.cursor()
    cursor.executemany(sql_query, sql_values)
    print("Успешная загрузка данных!")
    conn.commit()
    conn.close()
except Exception as e:
    print("Ошибка загрузки данных:", e)
    conn.close()
