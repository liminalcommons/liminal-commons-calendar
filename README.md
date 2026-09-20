# Liminal Commons Calendar — Erik's Vibecoding Gateway

This is **not a finished bot**. It is a Telegram-based gateway for Erik to
vibecode the Liminal Commons calendar with AI coding agents.

## What it does

- This bot **is** Hermes Agent for the Liminal Commons calendar.
- Receives messages from Erik on Telegram (`@Erikliminalcommonsbot`).
- Logs everything to a local SQLite database (`data/gateway.db`).
- Runs Hermes Agent by default; can also dispatch OpenCode:
  - `/hermes <prompt>` → Hermes Agent (default)
  - `/opencode <prompt>` → OpenCode
- Reports agent output back to Telegram.

## Quick start

1. Copy `.env.example` to `.env` and add the real bot token.
2. Run directly on the host (recommended for vibecoding):
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python bot.py
   ```
3. Or run in Docker:
   ```bash
   make up
   make logs
   ```

## Telegram usage

```
/hermes add an /events command that lists calendar entries
@opencode write a test for the database schema
/status
/cancel 3
/history
```

## Dev helpers

### Windows

```powershell
.\scripts\dev.ps1 up
.\scripts\dev.ps1 logs
.\scripts\dev.ps1 test-token
```

### macOS / Linux / WSL

```bash
make up        # start bot
make logs      # follow logs
make test      # verify Telegram token
make down      # stop bot
```

## Project context for agents

- `CLAUDE.md` — project intent and rules
- `.hermes.md` — Hermes-specific context
- `AGENTS.md` — generic agent instructions

## Persistence

- `data/gateway.db` — SQLite: messages + agent run history
- `data/agent_logs/` — stdout/stderr from agent runs
- Both are gitignored.

## CI

GitHub Actions builds the Docker image on every push. It uses:
- `ERIK_BOT_TOKEN` secret to verify the bot token
- `BOT_GITHUB_TOKEN` secret for sync smoke tests
