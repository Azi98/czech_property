import json
import re

with open("czech_law_resources.json", "r", encoding="utf-8") as f:
    documents = json.load(f)

with open("zakon_67_2013.json", "r", encoding="utf-8") as f:
    new_documents = json.load(f)


documents.extend(new_documents)

with open("extended_law_resources.json", "w", encoding="utf-8") as f:
    json.dump(documents, f, ensure_ascii=False, indent=2)

#with open("czech_law_resources.json", "w", encoding="utf-8") as f:
#    json.dump(documents, f, ensure_ascii=False, indent=2)

#print("Section name были успешно обновлены и сохранены в czech_law_resources.json")