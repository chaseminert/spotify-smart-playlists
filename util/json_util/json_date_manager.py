import json
from datetime import date
import re

# 1. THE ENCODER
class DateEncoder(json.JSONEncoder):
    """Converts Python date objects into ISO-8601 string format."""
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()  # Returns 'YYYY-MM-DD'
        return super().default(obj)

# 2. THE DECODER HOOK
# Matches 'YYYY-MM-DD' format exactly
_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def date_decoder_hook(dct):
    """Scans JSON dictionaries and converts ISO date strings back into date objects."""
    for key, value in dct.items():
        if isinstance(value, str) and _DATE_REGEX.match(value):
            try:
                dct[key] = date.fromisoformat(value)
            except ValueError:
                pass  # Skip if it looks like a date but is invalid (e.g., 2026-02-31)
    return dct
