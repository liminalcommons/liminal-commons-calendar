# Agent instructions for Liminal Commons Calendar

## Goal

This Telegram bot is a surface of Hermes Agent. Help Erik vibecode a Telegram-based calendar for Liminal Commons.

## When editing this repo

1. Read `CLAUDE.md` and `.hermes.md` first.
2. Hermes Agent is the default brain; OpenCode is the only alternate agent.
3. Make minimal, focused changes.
4. Run `python -m py_compile bot.py` after editing Python.
5. If you add dependencies, update `requirements.txt` and `Dockerfile`.
6. Update `README.md` if user-facing behavior changes.
7. Commit with clear messages when Erik asks.

## Testing

- `make test` — verify Telegram token.
- `python bot.py` — local smoke test (requires `.env`).
- `docker compose up -d --build` — container smoke test.

## Agent preferences

- Prefer async Python with `python-telegram-bot`.
- Keep SQLite schema migrations additive (new tables/columns).
- Use `pathlib` for paths.
