"""
Получает на вход схему базу данных, запрос от концового пользователя и отправляет запрос в LLM, для создания SQL Запроса. Отправляет два запроса языковой модели -
На первом шаге просит LLM из схемы базы данных взять только нужные для создания запроса колонки, а во втором запросе передает эти колонки для создания запроса. 
"""

from dotenv import load_dotenv
import os
from openai import OpenAI
import json

# Load variables from the .env file
load_dotenv()

# Access the API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI()

#db_schema string parameter is the name of JSON file with database schema and user_prompt is a string with user's prompt
def create_sql_request(db_schema, user_prompt, debug=False):

    # Open the JSON file
    with open(db_schema, "r", encoding="utf-8") as f:
        db_schema = json.load(f)

    # Convert the structure into a string for sending in a prompt
    db_schema_str = json.dumps(db_schema, ensure_ascii=False, indent=2)

    # Example of using the database structure in a prompt
    prompt_1 = f"""
    We have the following database structure:
    {db_schema_str}

    The user has requested: "{user_prompt}".
    Based on the database structure, indicate which columns should be used in the SQL query.

    Important notes:
    1. The values in the columns are **strictly limited** to those listed in the "Options" section.
    2. Do not generalize or modify the values. Use them exactly as they are listed.
    3. Include the table name, column names, their data types, and detailed descriptions with all possible row values (from "Options").

    Output example:

    "Table name: Properties

    Relevant columns:

    1. **Layout**
    - **Type:** VARCHAR(10)
    - **Description:** Layout of the property
    - **Options:** Garsoniéra, 1+kk, 1+1, 2+1, 2+kk, 3+kk, 3+1, 4+kk, 4+1, 5+kk, 5+1, 6+kk, 6+1

    2. **Furnished**
    - **Type:** VARCHAR(15)
    - **Description:** Furnishing status of the property
    - **Options:** Cástecne, Vybaveno, Null

    3. **Price**
    - **Type:** INT
    - **Description:** Price of the property"
    """

    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f"{prompt_1}"
            }
        ]
    )

    first_answer = (completion.choices[0].message.content)

    # Если debug=True, выводим first_answer
    if debug:
        print("First Answer from LLM:")
        print(first_answer)

    prompt_2 = f"""
    The user requested: {user_prompt}

    The table name, the columns required, and row options to form the SQL query are as follows: {first_answer}

    Important notes for generating the SQL query:
    1. Use the syntax compatible with **Postgres SQL**.
    2. Match column values exactly as specified in the "Options". Do not generalize or modify them.
    3. Ensure all conditions are properly formed, including the full value descriptions (e.g., "A - Mimořádně úsporná").

    Generate a ready-to-use SQL query to retrieve the information requested by the user. The response should include only the SQL query.
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f"{prompt_2}"
            }
        ]
    )

    # Get the content of the response and clean it
    sql_query = completion.choices[0].message.content.strip()

    # Remove formatting like ```sql and ```
    if sql_query.startswith("```sql"):
        sql_query = sql_query[6:]  # Remove the starting ```sql
    if sql_query.endswith("```"):
        sql_query = sql_query[:-3]  # Remove the ending ```

    if debug:
        print("Generated SQL Query:")
        print(sql_query)

    return sql_query.strip()  # Ensure there are no extra spaces



if __name__ == "__main__":
    print(create_sql_request("../data/db_schema.json", "Назови среднюю цену трехкомнатных квартир в Праге"))