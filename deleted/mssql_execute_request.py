import pyodbc

def execute_query(sql_query: str) -> None:
    """
    Просто выполняет переданный SQL-запрос и выводит результаты.
    """
    
    # Настраиваем параметры подключения к базе данных
    SERVER = 'property09.database.windows.net'
    DATABASE = 'property_db'
    USERNAME = 'azna09'
    PASSWORD = 'BedaStudentSeptember2024!'

    connection_string = (
        f'DRIVER={{ODBC Driver 18 for SQL Server}};'
        f'SERVER={SERVER};DATABASE={DATABASE};'
        f'UID={USERNAME};PWD={PASSWORD}'
    )

    try:
        # Подключаемся к базе
        conn = pyodbc.connect(connection_string)
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
        
    except pyodbc.Error as err:
        print(f"Ошибка при работе с базой данных: {err}")

    finally:
        # Закрываем соединение
        cursor.close()
        conn.close()

if __name__ == "__main__":
    execute_query("""SELECT AVG(Price) AS AveragePrice
                    FROM properties
                    WHERE Layout IN ('3+kk', '3+1') AND City = 'Praha';""")