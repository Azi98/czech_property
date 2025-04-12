"""
Причесывает значения полученные после scraping с Bezrealitky, получает json файлик и возвращает json файлик
"""

import json
from datetime import datetime
from typing import Union

# Функции для очистки
def clean_price(value: str) -> Union[int, None]:
    try:
        return int(value.replace('Kč', '').replace('\xa0', '').replace(' ', '').strip())
    except (ValueError, AttributeError):
        return None

def clean_date(value: str) -> Union[str, None]:
    try:
        value = value.strip()
        date_formats = ['%d. %m. %Y', '%Y-%m-%d']
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(value, fmt).date()
                return date_obj.isoformat()
            except ValueError:
                continue
        return None
    except AttributeError:
        return None

def clean_area(value: str) -> Union[int, None]:
    try:
        return int(value.replace('m²', '').replace(' ', '').strip())
    except (ValueError, AttributeError):
        return None

def clean_price_per_unit(value: str) -> Union[int, None]:
    try:
        return int(value.replace('Kč/ m2', '').replace('\xa0', '').replace(' ', '').strip())
    except (ValueError, AttributeError):
        return None

def clean_default(value: str) -> str:
    return value.replace('\xa0', '').strip()

def clean_floor(value: str) -> dict:
    """
    Обрабатывает значение "Podlaží" и возвращает два новых ключа: "floor" и "total_floors".
    Если данные некорректны, возвращает floor=None, total_floors=None.
    """
    try:
        # Пример: "2. podlaží z 2"
        parts = value.lower().replace('podlaží', '').strip().split('z')
        floor = int(parts[0].replace('.', '').strip())
        total_floors = int(parts[1].strip()) if len(parts) > 1 else None
        return {"Podlaží": floor, "Počet_Podlaží": total_floors}
    except (ValueError, IndexError, AttributeError):
        return {"Podlaží": None, "Počet_Podlaží": None}

def clean_property_data(raw_data: dict) -> dict:
    field_processors = {
        'Cena': clean_price,
        'Poplatky za služby': clean_price,
        'Administrativní poplatek': clean_price,
        'Poplatky za energie': clean_price,
        'Vratná kauce': clean_price,
        'Dostupné od': clean_date,
        'Užitná plocha': clean_area,
        'Cena za jednotku': clean_price_per_unit,
    }

    cleaned = {}
    for key, value in raw_data.items():
        if key == "Podlaží":
            # Обрабатываем Podlaží отдельно
            floor_data = clean_floor(value)
            cleaned.update(floor_data)  # Добавляем "Podlaží" и "Počet_Podlaží"
        elif key in field_processors:
            try:
                cleaned[key] = field_processors[key](value)
            except Exception as e:
                print(f"Ошибка обработки поля '{key}': {e}")
                cleaned[key] = None
        else:
            cleaned[key] = clean_default(value) if isinstance(value, str) else value

    return cleaned

def process_json_file(input_file: str, output_file: str):
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        cleaned_data = [clean_property_data(item) for item in raw_data]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

        print(f"Очистка завершена. Результаты сохранены в '{output_file}'.")
    except FileNotFoundError:
        print(f"Файл '{input_file}' не найден.")
    except json.JSONDecodeError:
        print(f"Ошибка чтения JSON из файла '{input_file}'.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    process_json_file("../data/uncleaned_data_full.json", "../data/cleaned_properties_full.json")