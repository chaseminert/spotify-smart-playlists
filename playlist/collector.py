"""Collect recent Spotify play history and persist the latest timestamps."""

from dataclasses import dataclass
from datetime import datetime, timezone
import spotipy
from database.setup import SessionLocal
from database.models import Play
from logging_setup.logging_config import setup_logging
from .spotify import get_track_isrc, get_spotify_client

logger = setup_logging()


@dataclass
class UpsertInfo:
    """Counts of inserted and updated play-history records."""
    inserted: int = 0
    updated: int = 0


def run(sp: spotipy.Spotify) -> UpsertInfo:
    """Fetch recently played tracks and upsert them into the local database."""
    upsert_info = UpsertInfo()
    data = sp.current_user_recently_played(limit=50)
    recently_played = data['items']


    with SessionLocal() as session:
        for item in recently_played:
            track = item.get('track')
            if not track or not track.get('id'):
                continue

            track_isrc = get_track_isrc(track)
            if track_isrc is None:
                continue


            last_played: datetime = normalize_last_played(item['played_at'])
            upsert_last_played(session, track_isrc, last_played, upsert_info)
        session.commit()

        if upsert_info.updated > 0 or upsert_info.inserted > 0:
            logger.info("Update complete")
            logger.info(f"Tracks inserted: {upsert_info.inserted}")
            logger.info(f"Tracks updated: {upsert_info.updated}")

        return upsert_info


def upsert_last_played(session, track_isrc: str, last_played: datetime, upsert_info: UpsertInfo) -> None:
    """
    Insert a new ``Play`` row or update the tracked timestamp when newer.
    """
    play = session.get(Play, track_isrc)

    if play:
        if last_played > play.last_played:
            play.last_played = last_played
            logger.debug(f"Updating track last played (id={track_isrc}) to {last_played}")

            upsert_info.updated += 1
    else:
        play = Play(
            track_isrc=track_isrc,
            last_played=last_played
        )
        session.add(play)
        upsert_info.inserted += 1
        logger.debug(f"Inserted new track: (id={track_isrc})")


def normalize_last_played(last_played_raw: str) -> datetime:
    """Normalize Spotify timestamps to naive UTC for SQLite persistence."""
    return (datetime.fromisoformat(last_played_raw.replace("Z", "+00:00"))
            .astimezone(timezone.utc)).replace(tzinfo=None)

if __name__ == '__main__':
    from spotify import get_spotify_client, get_track_isrc

    run(get_spotify_client())
