import os
from pathlib import Path
import json

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"
SCHEMA_JSON = data_dir / "db_schema.json"

with SCHEMA_JSON.open("r", encoding="utf-8") as f:
    db_schema = json.load(f)
    db_schema_str = json.dumps(db_schema, ensure_ascii=False, indent=2)

print(type(SCHEMA_JSON))