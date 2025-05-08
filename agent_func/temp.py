from langchain_community.utilities import SQLDatabase


DB_SETTINGS = {
    "dbname": "property_info",
    "user": "postgres",
    "password": "250998",
    "host": "localhost",
    "port": 5432
}


db = SQLDatabase.from_uri(f"postgresql://{DB_SETTINGS['user']}:{DB_SETTINGS['password']}@{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['dbname']}")

print(db.get_table_info())