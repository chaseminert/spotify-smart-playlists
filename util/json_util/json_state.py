from typing import Any
from settings import get_settings
from datetime import date
import json
import re

from util.json_util.json_date_manager import DateEncoder

settings = get_settings()


def update_json_state(key: str, val: Any) -> None:
    """
    Writes a key and value to the state dict, and then saves it to the JSON file
    """
    settings.STATE_DATA[key] = val
    with open(settings.STATE_PATH, "w") as file:
        json.dump(settings.STATE_DATA, file, cls=DateEncoder)


