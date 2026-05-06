"""Create and rebuild derived Spotify playlists from template playlists."""

from database.models import Play
from database.setup import SessionLocal
import spotipy
from datetime import datetime
from logging_setup.logging_config import setup_logging
from .spotify import get_spotify_client, get_playlist_length, get_playlist_tracks, add_songs_to_playlist, \
    get_playlists, get_current_track_isrc, get_track_isrc
import settings
logger = setup_logging()


def run(sp: spotipy.Spotify):
    """Ensure smart playlists exist, then rebuild each one from its template."""
    ensure_smart_playlists_exist(sp)
    current_track_isrc = get_current_track_isrc(sp)

    logger.debug(f"Got current track isrc ({current_track_isrc=})")

    playlists = get_playlists(sp)
    with SessionLocal() as session:
        for name, playlist in playlists.items():
            if not name.endswith(settings.TEMPLATE_SUFFIX):
                continue

            og_name = name[:-len(settings.TEMPLATE_SUFFIX)-1]

            template_id = playlist["id"]
            smart_name = name.replace(settings.TEMPLATE_SUFFIX, settings.SMART_SUFFIX)

            smart_playlist = playlists.get(smart_name)

            if smart_playlist is None:
                #  This should not happen if the smart playlist function works
                logger.critical(f"Smart playlist missing for {name}")
                exit(1)

            smart_id = smart_playlist["id"]

            rebuild_smart_playlist(sp, session, template_id, smart_id, og_name, current_track_isrc)


def ensure_smart_playlists_exist(sp):
    """
    Create missing smart playlists for every configured template playlist.

    A template playlist is any playlist whose name ends with
    ``settings.TEMPLATE_SUFFIX``. For each template, this function ensures that
    a sibling playlist ending with ``settings.SMART_SUFFIX`` exists.
    """
    me = sp.me()
    user_id = me["id"]

    playlists = get_playlists(sp)

    for name, playlist in playlists.items():
        if not name.endswith(settings.TEMPLATE_SUFFIX):
            continue

        smart_name = name[:-len(settings.TEMPLATE_SUFFIX)] + settings.SMART_SUFFIX

        if smart_name not in playlists:
            logger.info(f"Creating new playlist: {smart_name}")
            sp.user_playlist_create(
                user=user_id,
                name=smart_name,
                public=False
            )
        else:
            logger.debug(f"Playlist already exists: {smart_name}")


def rebuild_smart_playlist(sp, session, template_id: str, smart_id: str, base_name: str, current_track_isrc: str | None):
    """
    Rebuild a smart playlist from the tracks in its template playlist.

    Tracks are included when either no play-history record exists for their
    ISRC, or the most recent play is older than the configured threshold for
    the playlist. The currently playing track is always excluded to avoid
    immediately re-adding music that is already in rotation.
    """
    logger.debug(f"Rebuilding smart playlist for '{base_name}'")

    logger.debug("Getting tracks")
    template_tracks = get_playlist_tracks(sp, template_id)
    logger.debug("Got tracks")

    ids_to_add = []

    json_playlist_data = settings.JSON_DATA['playlist_data'].get(base_name)

    num_days = None
    if json_playlist_data is not None:
        num_days = json_playlist_data.get('days_not_played')

    if num_days is None:
        logger.debug("Using default number of days")
        num_days = settings.NUM_DAYS_DEFAULT
    else:
        logger.debug("Using number of days from JSON")

    logger.debug(f"Number of days: {num_days}")

    for item in template_tracks:
        track = item.get("track")
        if not track or not track.get("id"):
            continue

        track_id = track["id"]
        track_isrc = get_track_isrc(track)

        if track_isrc == current_track_isrc:
            logger.debug("Skipping currently playing track")
            continue

        play = session.get(Play, track_isrc)

        if play is None or not play.played_within_last_n_days(num_days):
            ids_to_add.append(track_id)

    old_len = get_playlist_length(sp, smart_id)

    add_songs_to_playlist(sp, smart_id, ids_to_add, wipe=True, shuffle=settings.SHUFFLE_ON_REBUILD)

    created_at = datetime.now(settings.DISPLAY_TZ).strftime("%m-%d-%y %I:%M %p")
    playlist_desc = f"Updated at: {created_at}"

    sp.playlist_change_details(playlist_id=smart_id, description=playlist_desc)
    logger.debug(f"Playlist description set for id {smart_id}: '{playlist_desc}'")
    new_len = get_playlist_length(sp, smart_id)

    logger.info(f"Created smart playlist for '{base_name}'")
    if new_len != old_len:
        logger.info(f"{old_len} tracks -> {new_len} tracks")


if __name__ == '__main__':
    run(get_spotify_client())
