"""Spotify API helpers shared across collection and playlist rebuild flows."""

from pathlib import Path

from spotipy import CacheFileHandler

import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
from datetime import timezone
import random

from database.setup import init_db
init_db()

UTC = timezone.utc

from logging_setup.logging_config import setup_logging

logger = setup_logging()


def get_spotify_client(require_token_cache: bool = True) -> spotipy.Spotify:
    """
    Build an authenticated Spotipy client with token caching enabled.

    First-time authorization must be completed interactively so Spotify can
    issue the initial refresh token. Subsequent runs reuse the cached token.
    """
    cache_path = Path(settings.SPOTIFY_CACHE_PATH)
    if require_token_cache and not cache_path.exists():
        raise FileNotFoundError(
            "Spotify token cache not found at "
            f"{cache_path}. Run `docker compose run --rm app --auth-only` "
            "to authenticate once before starting the scheduler."
        )

    if not require_token_cache and cache_path.exists():
        cache_path.unlink(missing_ok=True)
        logger.debug("Wiped old token cache directory before authentication")

    cache_handler = CacheFileHandler(cache_path=str(settings.SPOTIFY_CACHE_PATH))

    auth_manager = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope=settings.SPOTIFY_SCOPE,
        cache_handler=cache_handler,
        open_browser=False,  # good default for headless; first run you'll copy/paste URL
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    try:
        sp.current_user()
        logger.info("Spotify authentication successful.")
        return sp
    except spotipy.exceptions.SpotifyOauthError as exc:
        exc_text = str(exc).lower()
        if "invalid_grant" in exc_text:
            logger.critical(
            "Spotify refresh token has expired after 6 months. "
            "Run `docker compose run --rm app --auth-only` to re-authenticate and retrieve a new refresh token")
            exit(-1)
        else:
            raise


def get_playlist_length(sp: spotipy.Spotify, playlist_id):
    """Return the total number of tracks currently in a playlist."""
    playlist = sp.playlist(playlist_id)
    return playlist['tracks']['total']


def get_track_isrc(track: dict):
    """Extract a track's ISRC, logging when Spotify omits the identifier."""
    isrc = track.get("external_ids", {}).get("isrc")
    if isrc is None:
        logger.warning(f"Track is missing ISRC: '{track['id']}'")
    return isrc


def get_playlists(sp: spotipy.Spotify) -> dict[str, dict]:
    """Fetch all playlists for the current user, keyed by playlist name."""
    playlists = []
    results = sp.current_user_playlists(limit=50)
    playlists += results["items"]

    while results["next"]:
        results = sp.next(results)
        playlists += results["items"]

    playlist_names = {p["name"]: p for p in playlists}

    return playlist_names


def get_playlist_tracks(sp: spotipy.Spotify, playlist_id) -> list[dict]:
    """Fetch every track item from a playlist, following Spotify pagination."""
    tracks = []
    results = sp.playlist_items(playlist_id, limit=100)

    tracks += results["items"]

    while results["next"]:
        results = sp.next(results)
        tracks += results["items"]

    return tracks


def wipe_playlist(sp: spotipy.Spotify, playlist_id):
    """Remove all tracks from a playlist before repopulating it."""
    sp.playlist_replace_items(playlist_id, [])
    logger.debug("Playlist wiped")


def add_songs_to_playlist(sp: spotipy.Spotify, playlist_id: str, song_ids: list[str], wipe=False, shuffle=False):
    """Add tracks to a playlist, optionally wiping or shuffling first."""
    if wipe:
        wipe_playlist(sp, playlist_id)

    if shuffle:
        # Preserve the original list so callers do not observe in-place mutation.
        song_ids = random.sample(song_ids, len(song_ids))

    for i in range(0, len(song_ids), 100):
        sp.playlist_add_items(playlist_id, song_ids[i:i+100])
    logger.debug(f"Added {len(song_ids)} to playlist")


def get_current_track_isrc(sp) -> str | None:
    """Return the ISRC for the current track, or ``None`` when unavailable."""
    playback = sp.current_user_playing_track()

    # Spotify returns ``None`` when nothing is actively playing.
    if not playback:
        return None

    item = playback.get('item')
    if item is None:
        return None

    return get_track_isrc(item)


def track_id_to_isrc(sp: spotipy.Spotify, track_id: str):
    """Resolve a Spotify track ID to its ISRC."""
    track = sp.track(track_id)
    return get_track_isrc(track)


def shuffle_playlist(sp: spotipy.Spotify, playlist_id: str):
    """Shuffle an existing playlist in place and stamp its description."""
    playlist_tracks = get_playlist_tracks(sp, playlist_id)
    song_ids = []
    for item in playlist_tracks:
        track = item.get("track")
        if not track or not track.get("id"):
            continue

        track_id = track["id"]
        song_ids.append(track_id)
    random.shuffle(song_ids)
    add_songs_to_playlist(sp, playlist_id, song_ids, wipe=True)

    shuffled_at = datetime.now(settings.DISPLAY_TZ).strftime("%m-%d-%y %I:%M %p")
    playlist_desc = f"Last shuffled: {shuffled_at}"

    sp.playlist_change_details(playlist_id=playlist_id, description=playlist_desc)
    logger.debug(f"Playlist description set for id {playlist_id}: '{playlist_desc}'")

    logger.debug(f"Shuffled playlist: {playlist_id}")

