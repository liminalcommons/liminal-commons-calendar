# Developing Erik / Liminal Commons Calendar Bot

## Local quick start

1. Clone the repo.
2. Copy `.env.example` to `.env` and add the real token.
3. Start the bot on the host (recommended for vibecoding):
   - **Windows**: `.\scripts\dev.ps1 run-host`
   - **Linux/macOS**: `make run-host`
4. Or run in Docker:
   - **Windows**: `.\scripts\dev.ps1 up`
   - **Linux/macOS**: `make up`

## Vibecoding with Hermes

This bot is a surface of Hermes Agent. In Telegram:

```
/hermes add an /events command
@opencode write a test for the database schema
/status
/cancel 1
/history
```

## Two-way GitHub sync

To push changes back to GitHub when agents edit the repo:

1. Create a fine-grained personal access token with read/write access to `liminalcommons/liminal-commons-calendar`.
2. Add it to `.env` as `GITHUB_TOKEN=`.
3. Restart the bot.

## CI

GitHub Actions builds the Docker image on every push. The workflow uses the `ERIK_BOT_TOKEN` secret to verify the token still works.
