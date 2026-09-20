#!/usr/bin/env bash
set -euo pipefail

# Pull/push events.json with GitHub if configured
if [ -n "${GITHUB_TOKEN:-}" ] && [ -f /app/scripts/sync_repo.py ]; then
    python3 /app/scripts/sync_repo.py
fi

# Start the bot (or run the overridden command)
exec "$@"
