import json
from datetime import date

from util.json_util.json_date_manager import DateEncoder, date_decoder_hook


def test_date_encoder_serializes_date_to_iso_string():
    payload = json.dumps({"token_expires_on": date(2026, 7, 27)}, cls=DateEncoder)

    assert payload == '{"token_expires_on": "2026-07-27"}'


def test_date_decoder_hook_converts_iso_date_strings():
    payload = '{"token_expires_on": "2026-07-27", "name": "daily"}'

    decoded = json.loads(payload, object_hook=date_decoder_hook)

    assert decoded["token_expires_on"] == date(2026, 7, 27)
    assert decoded["name"] == "daily"


def test_date_decoder_hook_leaves_invalid_dates_unchanged():
    payload = '{"token_expires_on": "2026-02-31"}'

    decoded = json.loads(payload, object_hook=date_decoder_hook)

    assert decoded["token_expires_on"] == "2026-02-31"
