"""Application settings loaded from environment variables and ``config.json``."""

import json
import pytz
import os
from pathlib import Path
from logging_setup.logging_config import setup_logging

logger = setup_logging()

# ``DISPLAY_TZ`` is required so user-facing timestamps stay aligned with the
# deployment environment instead of always being shown in UTC.
DISPLAY_TZ = pytz.timezone(os.environ["DISPLAY_TZ"])
JSON_PATH = Path(__file__).parent / "config.json"
if not JSON_PATH.exists():
    logger.critical(f"JSON path does not exist: {JSON_PATH}")
    exit(-1)

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
if SPOTIFY_CLIENT_ID is None:
    logger.critical("SPOTIFY_CLIENT_ID is missing from environment")
    exit(-1)

SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
if SPOTIFY_CLIENT_SECRET is None:
    logger.critical("SPOTIFY_CLIENT_SECRET is missing from environment")
    exit(-1)

spotipy_cache_dir = Path(__file__).parent / '.spotipy-cache'
spotipy_cache_dir.mkdir(exist_ok=True)

SPOTIFY_CACHE_PATH = str(spotipy_cache_dir / 'token-cache')

# Only need recently played for the collector
SPOTIFY_SCOPE = (
    "user-read-recently-played "
    "playlist-read-private "
    "playlist-modify-private "
    "playlist-modify-public "
    "user-read-currently-playing"
)

SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

with open(JSON_PATH, 'r') as file:
    JSON_DATA: dict = json.load(file)

# Playlist naming and rebuild rules come from repository-local JSON so they can
# be changed without rebuilding the container image.
TEMPLATE_SUFFIX = JSON_DATA.get('template_suffix', "Template")

SMART_SUFFIX = JSON_DATA.get('smart_suffix', "Smart")

SHUFFLE_ON_REBUILD = bool(JSON_DATA.get('shuffle_on_rebuild', False))

NUM_DAYS_DEFAULT = int(JSON_DATA.get('days_not_played_default', 21))
