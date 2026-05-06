"""Interactive helper for manually shuffling an existing Spotify playlist."""

from dotenv import load_dotenv
load_dotenv()
from .spotify import get_spotify_client, shuffle_playlist, get_playlists


def main():
    """Prompt for playlist names and shuffle matching playlists in place."""
    sp = get_spotify_client()
    while True:
        playlist_name = input("Enter a base playlist name: ").strip()

        if playlist_name.lower() == 'quit':
            break
        playlists: dict[str, dict] = get_playlists(sp)
        target_playlist_id = None
        for name, playlist in playlists.items():
            if name.lower().strip() == playlist_name.lower():
                target_playlist_id = playlist['id']
                break

        if target_playlist_id is None:
            print(f"Error: No playlist found with the name '{playlist_name}'")
            continue

        shuffle_playlist(sp, target_playlist_id)
        print(f"Playlist '{playlist_name}' has been shuffled")
    print("goodbye!")


if __name__ == '__main__':
    main()
