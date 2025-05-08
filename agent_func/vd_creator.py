"""Это код для создания векторной базы данных.

Запустите его, чтобы создать векторную базу данных.

"""

import getpass
import os
from dotenv import load_dotenv
import json
from langchain_community.document_loaders import JSONLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from uuid import uuid4
from pathlib import Path

# Load variables from the .env file
load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

file_path='./extended_law_resources.json'
if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found at path: {file_path}")

data = json.loads(Path(file_path).read_text()) #загрузка данных из файла в виде списка словарей Python
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

vector_store = Chroma(
    collection_name="law_resources",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db"
)

# Define the metadata extraction function.
def metadata_func(record: dict, metadata: dict) -> dict:

    metadata["section_number"] = record.get("section_number")
    metadata["section_title"] = record.get("section_title")
    metadata["source_name"] = record.get("source")
    metadata["url"] = record.get("url")

    return metadata

#создание объектов Document из файлика json, который мы передаем в качестве аргумента
loader = JSONLoader(
    file_path=file_path,
    jq_schema='.[]',
    content_key="text",
    metadata_func=metadata_func
)

#как выглядит объект Document
"""Document(
    metadata={
        'source': '/Users/aznaur/Desktop/pet_project/property_price_project/rag/czech_civil_code.json',
        'seq_num': 68,
        'section_number': 2301,
        'section_title': 'Nájem bytu zvláštního určení',
        'source_name': 'Občanský zákoník č. 89/2012 Sb.',
        'url': 'https://www.zakonyprolidi.cz/cs/2012-89#p2301'
    },
    page_content=(
        "§ 2301\n\n"
        "(1) Zemře-li nájemce, nájem bytu zvláštního určení skončí a pronajímatel vyzve členy "
        "nájemcovy domácnosti, kteří v bytě žili ke dni smrti nájemce a nemají vlastní byt, aby "
        "byt vyklidili nejpozději do šesti měsíců ode dne, kdy výzvu obdrží. Nejsou-li v bytě "
        "takové osoby, pronajímatel vyzve nájemcovy dědice, aby byt vyklidili nejpozději do tří "
        "měsíců ode dne, kdy výzvu obdrží.\n\n"
        "(2) Pokud v bytě zvláštního určení žila ke dni smrti nájemce osoba zdravotně postižená "
        "nebo osoba, která dosáhla věku sedmdesáti let, která žila s nájemcem nejméně jeden rok "
        "ve společné domácnosti a nemá vlastní byt, přejde na ni nájem ke dni smrti nájemce, pokud "
        "se pronajímatel s touto osobou nedohodnou jinak.\n\n"
        "(3) Nájem bytu zvláštního určení může pronajímatel vypovědět pouze s předchozím souhlasem "
        "toho, kdo takový byt svým nákladem zřídil, popřípadě jeho právního nástupce."
    )
)
"""

documents = loader.load()

uuids = [str(uuid4()) for _ in range(len(documents))]

vector_store.add_documents(documents=documents, ids=uuids)

print(vector_store._collection.count())
