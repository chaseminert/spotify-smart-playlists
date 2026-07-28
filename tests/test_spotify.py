from playlist import spotify


class FakeSpotify:
    def __init__(self):
        self.added_batches = []
        self.replaced = []
        self.changed_details = []
        self.next_pages = []

    def current_user_playlists(self, limit):
        return {
            "items": [{"name": "First", "id": "playlist-1"}],
            "next": True,
        }

    def playlist_items(self, playlist_id, limit):
        return {
            "items": [{"track": {"id": "track-1"}}],
            "next": True,
        }

    def next(self, results):
        return self.next_pages.pop(0)

    def playlist_replace_items(self, playlist_id, items):
        self.replaced.append((playlist_id, items))

    def playlist_add_items(self, playlist_id, items):
        self.added_batches.append((playlist_id, items))

    def current_user_playing_track(self):
        return self.playback

    def playlist_change_details(self, playlist_id, description):
        self.changed_details.append((playlist_id, description))


def test_get_playlists_follows_pagination():
    sp = FakeSpotify()
    sp.next_pages = [
        {"items": [{"name": "Second", "id": "playlist-2"}], "next": False},
    ]

    playlists = spotify.get_playlists(sp)

    assert playlists == {
        "First": {"name": "First", "id": "playlist-1"},
        "Second": {"name": "Second", "id": "playlist-2"},
    }


def test_get_playlist_tracks_follows_pagination():
    sp = FakeSpotify()
    sp.next_pages = [
        {"items": [{"track": {"id": "track-2"}}], "next": False},
    ]

    tracks = spotify.get_playlist_tracks(sp, "playlist-1")

    assert tracks == [{"track": {"id": "track-1"}}, {"track": {"id": "track-2"}}]


def test_add_songs_to_playlist_wipes_and_batches_tracks():
    sp = FakeSpotify()
    song_ids = [f"track-{i}" for i in range(205)]

    spotify.add_songs_to_playlist(sp, "playlist-1", song_ids, wipe=True)

    assert sp.replaced == [("playlist-1", [])]
    assert [len(batch) for _, batch in sp.added_batches] == [100, 100, 5]
    assert sp.added_batches[0][1] == song_ids[:100]
    assert sp.added_batches[2][1] == song_ids[200:]


def test_add_songs_to_playlist_shuffle_does_not_mutate_input(monkeypatch):
    sp = FakeSpotify()
    song_ids = ["track-1", "track-2", "track-3"]
    monkeypatch.setattr(spotify.random, "sample", lambda items, count: list(reversed(items)))

    spotify.add_songs_to_playlist(sp, "playlist-1", song_ids, shuffle=True)

    assert song_ids == ["track-1", "track-2", "track-3"]
    assert sp.added_batches == [("playlist-1", ["track-3", "track-2", "track-1"])]


def test_get_current_track_isrc_handles_missing_playback():
    sp = FakeSpotify()
    sp.playback = None

    assert spotify.get_current_track_isrc(sp) is None


def test_get_current_track_isrc_returns_current_item_isrc():
    sp = FakeSpotify()
    sp.playback = {"item": {"id": "track-1", "external_ids": {"isrc": "USRC17607839"}}}

    assert spotify.get_current_track_isrc(sp) == "USRC17607839"
