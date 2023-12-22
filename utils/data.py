import json
from typing import Any

DATA_PATH = "./utils/"

with open(f"{DATA_PATH}books.json") as file:
    BOOKS: dict[str, Any] = json.load(file)

with open(f"{DATA_PATH}mappings.json") as file:
    VERSIONS: dict[str, str] = json.load(file)