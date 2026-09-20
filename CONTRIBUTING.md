# Developing Erik / Liminal Commons Calendar Bot

## Local quick start

1. Clone the repo.
2. Copy `.env.example` to `.env` and add the real token.
3. Start the bot:
   - **Windows**: `\.scripts\dev.ps1 up`
   - **Linux/macOS**: `make up`
4. Follow logs: `make logs`

## Edit events from the repo

`events.json` is the source of truth. You can edit it directly in the repo; the bot merges remote and local copies on startup/sync.

## Two-way GitHub sync

To push events back to GitHub when `/add` or `/delete` is used:

1. Create a fine-grained personal access token with read/write access to `liminalcommons/liminal-commons-calendar`.
2. Add it to `.env` as `GITHUB_TOKEN=`.
3. Restart the bot.

## CI

GitHub Actions builds the Docker image on every push. The workflow uses the `ERIK_BOT_TOKEN` secret to verify the token still works.
