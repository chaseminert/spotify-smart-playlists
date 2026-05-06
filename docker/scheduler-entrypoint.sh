#!/bin/sh
set -eu

: "${CRON_SCHEDULE:?CRON_SCHEDULE is required}"
: "${RUN_ON_STARTUP:?RUN_ON_STARTUP is required}"

CRON_FILE="/tmp/spotify-smart-playlist.crontab"

mkdir -p /app/.spotipy-cache

if [ "$RUN_ON_STARTUP" = "true" ]; then
  echo "Running startup sync before scheduler begins"
  /app/docker/run-main.sh "$@"
fi

cat > "$CRON_FILE" <<EOF
$CRON_SCHEDULE /app/docker/run-main.sh $*
EOF

chmod 0644 "$CRON_FILE"

echo "Starting supercronic with schedule: $CRON_SCHEDULE"
exec /usr/local/bin/supercronic -passthrough-logs -quiet "$CRON_FILE"
