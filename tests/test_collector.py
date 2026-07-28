from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Play
from playlist.collector import UpsertInfo, normalize_last_played, upsert_last_played


def make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_normalize_last_played_returns_naive_utc_datetime():
    normalized = normalize_last_played("2026-07-27T18:30:00-06:00")

    assert normalized == datetime(2026, 7, 28, 0, 30)
    assert normalized.tzinfo is None


def test_upsert_last_played_inserts_new_track():
    session = make_session()
    upsert_info = UpsertInfo()

    upsert_last_played(session, "USRC17607839", datetime(2026, 7, 27, 12), upsert_info)
    session.flush()

    play = session.get(Play, "USRC17607839")
    assert play.last_played == datetime(2026, 7, 27, 12)
    assert upsert_info == UpsertInfo(inserted=1, updated=0)


def test_upsert_last_played_updates_existing_track_when_newer():
    session = make_session()
    session.add(Play(track_isrc="USRC17607839", last_played=datetime(2026, 7, 20, 12)))
    session.flush()
    upsert_info = UpsertInfo()

    upsert_last_played(session, "USRC17607839", datetime(2026, 7, 27, 12), upsert_info)
    session.flush()

    play = session.get(Play, "USRC17607839")
    assert play.last_played == datetime(2026, 7, 27, 12)
    assert upsert_info == UpsertInfo(inserted=0, updated=1)


def test_upsert_last_played_ignores_older_existing_track():
    session = make_session()
    session.add(Play(track_isrc="USRC17607839", last_played=datetime(2026, 7, 27, 12)))
    session.flush()
    upsert_info = UpsertInfo()

    upsert_last_played(session, "USRC17607839", datetime(2026, 7, 20, 12), upsert_info)
    session.flush()

    play = session.get(Play, "USRC17607839")
    assert play.last_played == datetime(2026, 7, 27, 12)
    assert upsert_info == UpsertInfo(inserted=0, updated=0)
