# Spotify Smart Playlist

Build and maintain Spotify playlists based on how recently you played each track.

This project watches your recent listening history, stores last-played timestamps in a local SQLite database, and rebuilds "smart" playlists from template playlists in your Spotify account.

The intended deployment path is Docker Compose on a Linux server or small VPS.

## How It Works

- Create one or more Spotify playlists whose names end with `Template`
- Add the songs you want to manage to those template playlists
- Run this project
- For each template playlist, the app creates or updates a corresponding playlist ending with `Smart`
- Only tracks that have not been played within your configured time window are added to the smart playlist

Example:

- `Gym Template` -> `Gym Smart`
- `90s Rock Template` -> `90s Rock Smart`

## Requirements

- Docker and Docker Compose
- A Spotify account
- A Spotify developer app with API credentials
- A Linux machine or VPS for scheduled execution

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/spotify-smart-playlist.git
cd spotify-smart-playlist
```

### 2. Create a Spotify developer app

1. Go to the Spotify Developer Dashboard.
2. Sign in with your Spotify account.
3. Create a new app.
4. Copy the app's `Client ID` and `Client Secret`.
5. In the app settings, add this redirect URI exactly:

```text
http://127.0.0.1:8888/callback
```

6. Save the app settings.

This project uses these Spotify permissions:

- `user-read-recently-played`
- `playlist-read-private`
- `playlist-modify-private`
- `playlist-modify-public`
- `user-read-currently-playing`

### 3. Create your local files

```bash
cp .env.example .env
cp config-template.json config.json
```

Then update `.env` and `config.json`.

`.env` example:

```dotenv
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
DISPLAY_TZ=America/Denver
CRON_SCHEDULE=0 * * * *
RUN_ON_STARTUP=false
```

`DISPLAY_TZ` is optional. If omitted, Docker Compose defaults it to `UTC`.

`config.json` example:

```json
{
  "template_suffix": "Template",
  "smart_suffix": "Smart",
  "shuffle_on_rebuild": false,
  "days_not_played_default": 21,
  "playlist_data": {
    "Gym": {
      "days_not_played": 10
    },
    "90s Rock": {
      "days_not_played": 30
    }
  }
}
```

### 4. Create your template playlists

In Spotify, create playlists ending with your configured template suffix.

Examples:

- `Gym Template`
- `Focus Template`
- `Sunday Template`

Add tracks to those playlists. The app will create matching smart playlists automatically on the first run.

### 5. Build the image

```bash
docker compose build
```

### 6. Authenticate Spotify once

The first run requires interactive Spotify authorization so the token cache can be written under `.spotipy-cache/`.

```bash
docker compose run --rm app --auth-only
```

Open the Spotify authorization URL, approve access, and paste the redirect URL back into the terminal when prompted.

If the callback page looks broken after approval, that is expected because of the configured redirect URL.

After a successful first run, you should have:

- `.spotipy-cache/` for Spotify auth tokens
- `database/history.db` for local play history
- log files under `logs/`

### 7. Start the scheduler

Normal scheduled runs:

```bash
docker compose up -d scheduler
```

Forced scheduled runs:

```bash
docker compose up -d scheduler_force
```

If you want the scheduler container to execute one sync immediately when it starts, set this in `.env`:

```dotenv
RUN_ON_STARTUP=true
```

## Docker Services

### `app`

The app supports two optional flags:

- `--auth-only`: authenticate Spotify and exit without running the pipeline
- `--force`: rebuild playlists even if the collector did not detect any new listening-history updates

Run the main pipeline once:

```bash
docker compose run --rm app
```

Run the pipeline once and force a rebuild:

```bash
docker compose run --rm app --force
```

Authenticate Spotify and exit without running the pipeline:

```bash
docker compose run --rm app --auth-only
```

### `scheduler`

Run the scheduler on the interval defined by `CRON_SCHEDULE`.

```bash
docker compose up -d scheduler
```

### `scheduler_force`

Run the scheduler on the interval defined by `CRON_SCHEDULE`, always passing `--force` to the pipeline.

```bash
docker compose up -d scheduler_force
```

Use `scheduler_force` if you want scheduled runs to rebuild playlists every time, even when no new listening-history records were collected.

### `shuffler`

Run the interactive playlist shuffler helper:

```bash
docker compose run --rm shuffler
```

## Configuration Reference

- `template_suffix`: suffix used to identify source playlists
- `smart_suffix`: suffix used for generated playlists
- `shuffle_on_rebuild`: whether rebuilt smart playlists should be shuffled before tracks are added
- `days_not_played_default`: fallback rule for playlists not explicitly listed below
- `playlist_data`: per-playlist overrides keyed by base playlist name

Important:

- The keys inside `playlist_data` must match the base playlist name exactly
- If your playlist is named `Gym Template`, the key must be `Gym`
- If a playlist is not listed in `playlist_data`, `days_not_played_default` is used
- `shuffle_on_rebuild` is a global setting and applies to every smart playlist rebuild

## Playlist Shuffler

This repo also includes a separate utility in playlist/playlist_shuffler.py.

It:

- prompts you for a playlist name
- looks up that playlist in your Spotify account
- rewrites the playlist in a randomized order
- updates the playlist description with the last shuffled time

Run it with Docker Compose:

```bash
docker compose run --rm shuffler
```

Run it locally:

```bash
venv/bin/python -m playlist.playlist_shuffler
```

Type `quit` to exit.

## Local Python Alternative

Docker Compose is the recommended way to run this project. If you prefer not to use containers, you can still run it directly with Python.

### 1. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

Local runs support the same optional flags:

- `--auth-only`: authenticate Spotify and exit without running the pipeline
- `--force`: rebuild playlists even if the collector did not detect any new listening-history updates

Normal run:

```bash
./run.sh
```

Forced run:

```bash
./run.sh --force
```

Auth only:

```bash
./run.sh --auth-only
```

### 4. Optional host cron

If you use the non-Docker flow, you can schedule it directly on the host:

```cron
0 * * * * /path/to/spotify-smart-playlist/run.sh
```

## Troubleshooting

### `SPOTIFY_CLIENT_ID is missing from environment`

Your credentials are not available in the container or local shell. Make sure `.env` exists and includes:

```dotenv
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
```

### `JSON path does not exist`

You have not created `config.json`. Copy `config-template.json` to `config.json` and edit it.

### The smart playlist was created but is empty

Possible reasons:

- all tracks were played recently
- the playlist name in `playlist_data` does not match the base playlist name

## Notes

- This project stores state locally and is intended to be run by a single user for their own Spotify account.
- Smart playlists are only shuffled on rebuild if `shuffle_on_rebuild` is set to `true` in `config.json`.
- The app does not delete your template playlists.
