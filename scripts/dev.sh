#!/usr/bin/env bash
# Liminal Commons Calendar Bot - dev helpers for Erik on macOS/Linux
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_env() {
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "Created .env from example. Please edit it with the real token."
        exit 1
    fi
}

cmd="${1:-up}"

case "$cmd" in
    build)
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" build
        ;;
    up)
        require_env
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" up -d --build
        echo "Bot is running. Logs: ./scripts/dev.sh logs"
        ;;
    down)
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" down
        ;;
    logs)
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" logs -f bot
        ;;
    shell)
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" exec bot bash
        ;;
    test-token)
        require_env
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm bot python -c "from telegram import Bot; import os, asyncio; bot = Bot(os.environ['ERIK_BOT_TOKEN']); print((await bot.get_me()).username)"
        ;;
    sync-repo)
        require_env
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm bot python scripts/sync_repo.py
        ;;
    *)
        echo "Usage: ./scripts/dev.sh [build|up|down|logs|shell|test-token|sync-repo]"
        exit 1
        ;;
esac
