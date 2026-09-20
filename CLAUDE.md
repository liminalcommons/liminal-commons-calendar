# Liminal Commons Calendar — Vibecoding Gateway

This repo is Erik's vibecoding workspace for the Liminal Commons community calendar.
It is NOT a finished product. The Telegram bot (`@Erikliminalcommonsbot`) is a thin
interface that forwards Erik's prompts to coding agents.

## Project intent

- Build a calendar system for Liminal Commons events.
- Telegram bot is the primary user interface for Erik.
- Code-first: agents edit this repo; humans review via git.

## Architecture

- `bot.py` — Telegram gateway. Logs messages to SQLite, dispatches to agents.
- `data/` — SQLite state + agent logs (gitignored).
- `scripts/` — dev helpers and sync utilities.
- `Dockerfile` / `docker-compose.yml` — containerized bot runtime.
- `.github/workflows/` — CI.

## Coding rules

1. Keep `bot.py` runnable as a plain Python script on the host for vibecoding.
2. Docker image must still build and run a minimal bot (agent spawning optional).
3. Use `python-telegram-bot` for Telegram interactions.
4. Store local state in `data/gateway.db` via SQLite.
5. Never commit secrets. `.env` and `data/` are gitignored.
6. Write tests for non-trivial logic.
7. Keep the README accurate.
