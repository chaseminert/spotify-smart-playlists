from datetime import datetime, timezone
from types import SimpleNamespace

from playlist import playlist_builder


class FakeSpotify:
    def __init__(self):
        self.created = []
        self.changed_details = []

    def me(self):
        return {"id": "user-1"}

    def user_playlist_create(self, user, name, public):
        self.created.append({"user": user, "name": name, "public": public})

    def playlist_change_details(self, playlist_id, description):
        self.changed_details.append({"playlist_id": playlist_id, "description": description})


class FakeSession:
    def __init__(self, plays):
        self.plays = plays

    def get(self, model, key):
        return self.plays.get(key)


class FakePlay:
    def __init__(self, played_recently):
        self.played_recently = played_recently

    def played_within_last_n_days(self, n):
        return self.played_recently


class FixedDateTime:
    @classmethod
    def now(cls, tz):
        return datetime(2026, 7, 27, 18, 30, tzinfo=tz)


def test_ensure_smart_playlists_exist_creates_missing_smart_playlist(monkeypatch):
    sp = FakeSpotify()
    monkeypatch.setattr(
        playlist_builder,
        "settings",
        SimpleNamespace(TEMPLATE_SUFFIX="Template", SMART_SUFFIX="Smart"),
    )
    monkeypatch.setattr(
        playlist_builder,
        "get_playlists",
        lambda sp: {
            "Gym Template": {"id": "template-1"},
            "Focus Template": {"id": "template-2"},
            "Focus Smart": {"id": "smart-2"},
        },
    )

    playlist_builder.ensure_smart_playlists_exist(sp)

    assert sp.created == [{"user": "user-1", "name": "Gym Smart", "public": False}]


def test_rebuild_smart_playlist_filters_tracks_and_updates_description(monkeypatch):
    sp = FakeSpotify()
    added_calls = []
    monkeypatch.setattr(
        playlist_builder,
        "settings",
        SimpleNamespace(
            JSON_DATA={"playlist_data": {"Gym": {"days_not_played": 10}}},
            NUM_DAYS_DEFAULT=21,
            SHUFFLE_ON_REBUILD=True,
            DISPLAY_TZ=timezone.utc,
        ),
    )
    monkeypatch.setattr(
        playlist_builder,
        "get_playlist_tracks",
        lambda sp, playlist_id: [
            {"track": {"id": "stale-track", "external_ids": {"isrc": "STALE"}}},
            {"track": {"id": "recent-track", "external_ids": {"isrc": "RECENT"}}},
            {"track": {"id": "current-track", "external_ids": {"isrc": "CURRENT"}}},
            {"track": {"external_ids": {"isrc": "NO_ID"}}},
            {"track": None},
        ],
    )
    monkeypatch.setattr(playlist_builder, "get_playlist_length", lambda sp, playlist_id: 7)
    monkeypatch.setattr(
        playlist_builder,
        "add_songs_to_playlist",
        lambda sp, playlist_id, ids, wipe, shuffle: added_calls.append(
            {
                "playlist_id": playlist_id,
                "ids": ids,
                "wipe": wipe,
                "shuffle": shuffle,
            }
        ),
    )
    monkeypatch.setattr(playlist_builder, "datetime", FixedDateTime)
    session = FakeSession(
        {
            "STALE": FakePlay(played_recently=False),
            "RECENT": FakePlay(played_recently=True),
        }
    )

    playlist_builder.rebuild_smart_playlist(
        sp,
        session,
        template_id="template-1",
        smart_id="smart-1",
        base_name="Gym",
        current_track_isrc="CURRENT",
    )

    assert added_calls == [
        {
            "playlist_id": "smart-1",
            "ids": ["stale-track"],
            "wipe": True,
            "shuffle": True,
        }
    ]
    assert sp.changed_details == [
        {"playlist_id": "smart-1", "description": "Updated at: 07-27-26 06:30 PM"}
    ]
