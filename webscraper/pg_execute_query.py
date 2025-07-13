import psycopg2
from psycopg2 import sql

def execute_query(sql_query: str):
    """
    Выполняет переданный SQL-запрос и возвращает результаты
    (если это SELECT-запрос) или строку о выполненном действии (INSERT, UPDATE, DELETE).
    """
    DB_SETTINGS = {
        "dbname": "property_project",
        "user": "postgres",
        "password": "250998",
        "host": "localhost",
        "port": 5432
    }

    conn = None
    cursor = None

    try:
        # Подключаемся к базе
        conn = psycopg2.connect(**DB_SETTINGS)
        cursor = conn.cursor()

        # Выполняем SQL-запрос
        cursor.execute(sql_query)

        # Определяем, является ли это SELECT-запросом
        if sql_query.strip().lower().startswith("select"):
            rows = cursor.fetchall()
            return rows  # Возвращаем список кортежей
        else:
            conn.commit()  # Для INSERT, UPDATE, DELETE
            return "Query executed and changes committed."

    except psycopg2.Error as err:
        # В случае ошибки вернём её описание
        return f"Ошибка при работе с базой данных: {err}"

    finally:
        # Закрываем соединение
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    # Пример использования: SELECT
    rows_result = execute_query("""SELECT price, layout 
                                   FROM properties
                                   LIMIT 10;""")
    print("Результат запроса:", rows_result)

    # Пример использования: INSERT
    insert_result = execute_query("""INSERT INTO properties (price, layout) 
                                    VALUES (12345, 'Studio');""")
    print("Результат запроса:", insert_result)
