"""
Просто выполняет переданный SQL-запрос и выводит результаты.
"""

import psycopg2
from psycopg2 import sql
import json

def execute_query(sql_query: str) -> None:

    
    # Настраиваем параметры подключения к базе данных
    DB_SETTINGS = {
    "dbname": "property_project",
    "user": "postgres",
    "password": "250998",
    "host": "localhost",
    "port": 5432
}

    try:
        # Подключаемся к базе
        conn = psycopg2.connect(**DB_SETTINGS)
        cursor = conn.cursor()

        # Выполняем SQL-запрос
        cursor.execute(sql_query)
        
        # Если это SELECT-запрос, нам нужно получить результаты
        if sql_query.strip().lower().startswith("select"):
            rows = cursor.fetchall()
            for row in rows:
                print(row)
        else:
            # Если это INSERT, UPDATE, DELETE и т.д., зафиксируем изменения
            conn.commit()
            print("Query executed and changes committed.")
        
    except psycopg2.Error as err:
        print(f"Ошибка при работе с базой данных: {err}")

    finally:
        # Закрываем соединение
        cursor.close()
        conn.close()

if __name__ == "__main__":
    execute_query("""SELECT price, layout 
                    FROM properties
                    LIMIT 10;""")