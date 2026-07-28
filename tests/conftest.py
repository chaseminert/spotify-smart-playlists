"""Shared pytest configuration for import-time application settings."""

from __future__ import annotations

import json
import os
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _ROOT / "config.json"
_CREATED_CONFIG = False


def pytest_configure():
    """Provide dummy local settings before modules import ``settings``."""
    global _CREATED_CONFIG

    os.environ.setdefault("DISPLAY_TZ", "UTC")
    os.environ.setdefault("SPOTIFY_CLIENT_ID", "test-client-id")
    os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test-client-secret")

    if not _CONFIG_PATH.exists():
        _CONFIG_PATH.write_text(
            json.dumps(
                {
                    "template_suffix": "Template",
                    "smart_suffix": "Smart",
                    "shuffle_on_rebuild": False,
                    "days_not_played_default": 21,
                    "playlist_data": {},
                }
            ),
            encoding="utf-8",
        )
        _CREATED_CONFIG = True


def pytest_unconfigure():
    """Remove only the config file this test suite created."""
    if _CREATED_CONFIG:
        _CONFIG_PATH.unlink(missing_ok=True)
