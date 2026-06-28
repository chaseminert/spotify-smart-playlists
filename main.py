"""Command-line entry point for the Spotify smart playlist pipeline."""

import argparse

from playlist import collector, playlist_builder
from playlist.collector import UpsertInfo

from logging_setup.logging_config import setup_logging
from playlist.spotify import get_spotify_client

logger = setup_logging()


def main():
    """Run authentication, collection, and playlist rebuild steps."""
    args = parse_args()
    sp = get_spotify_client(require_token_cache=not args.auth_only)
    if args.auth_only:
        logger.info("Authentication complete. Pipeline is ready to run.")
        return

    upsert_info: UpsertInfo = collector.run(sp)
    if upsert_info.updated == 0 and upsert_info.inserted == 0 and not args.force:
        logger.debug("Skipping playlist rebuild since nothing was updated.")
        return
    logger.info("Running playlist builder.")
    playlist_builder.run(sp)
    logger.info("Spotify smart playlist pipeline complete.")


def parse_args():
    """Parse supported command-line flags for the pipeline."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run playlist rebuilder regardless")
    parser.add_argument(
        "--auth-only",
        action="store_true",
        help="Authenticate Spotify and exit without running the pipeline")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Fatal error in Spotify pipeline")
        raise
