# Liminal Commons Calendar — Vibecoding Gateway

This repo is Erik's vibecoding workspace for the Liminal Commons community calendar.
It is NOT a finished product. The Telegram bot (`@Erikliminalcommonsbot`) is a thin
interface that forwards Erik's prompts to coding agents.

## Project intent

- Build a calendar system for Liminal Commons events.
- Telegram bot is the primary user interface for Erik.
- Code-first: agents edit this repo; humans review via git.

## Architecture

- `bot.py` — Telegram interface for Hermes Agent. Logs messages to SQLite, dispatches to agents.
- `data/` — SQLite state + agent logs (gitignored).
- `scripts/` — dev helpers and sync utilities.
- `Dockerfile` / `docker-compose.yml` — containerized bot runtime.
- `.github/workflows/` — CI.

## Coding rules

1. Hermes Agent is the default and primary brain. OpenCode is an optional alternate.
2. Keep `bot.py` runnable as a plain Python script on the host for vibecoding.
3. Docker image must still build and run a minimal bot (agent spawning optional).
4. Use `python-telegram-bot` for Telegram interactions.
5. Store local state in `data/gateway.db` via SQLite.
6. Never commit secrets. `.env` and `data/` are gitignored.
7. Write tests for non-trivial logic.
8. Keep the README accurate.
