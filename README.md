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

### BotFather commands

Send `botfather-commands.txt` to [@BotFather](https://t.me/botfather) with `/setcommands`.

## CI

GitHub Actions builds the Docker image on every push. Add `ERIK_BOT_TOKEN` to the repo's GitHub secrets if you want the CI smoke test to verify the token.

## GitHub integration

Set `GITHUB_TOKEN` and `GITHUB_REPO` in `.env`. The bot can sync `events.json` with the repo so events live in version control and Erik can edit them as code.
