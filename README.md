# Erik / Liminal Commons Calendar Bot

Telegram bot that manages the Liminal Commons community calendar.

## Quick start

1. Copy `.env.example` to `.env` and fill in values.
2. Run the bot:
   - Windows: `\.scripts\dev.ps1 up`
   - macOS/Linux: `./scripts/dev.sh up`
3. Message the bot on Telegram: `@Erikliminalcommonsbot`

## Commands

- `/start` — hello
- `/events` — list calendar
- `/add` — add an event (interactive)
- `/delete <id>` — delete an event
- `/cancel` — cancel current action

## Dev helpers

```bash
./scripts/dev.sh build        # rebuild image
./scripts/dev.sh logs         # follow logs
./scripts/dev.sh shell        # shell inside container
./scripts/dev.sh test-token   # verify Telegram token
./scripts/dev.sh sync-repo    # sync events with GitHub repo
```

## GitHub integration

Set `GITHUB_TOKEN` and `GITHUB_REPO` in `.env`. The bot can sync `events.json` with the repo so events live in version control and Erik can edit them as code.
