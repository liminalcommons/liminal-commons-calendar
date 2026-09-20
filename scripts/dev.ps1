# Liminal Commons Calendar Bot - dev helpers for Erik on Windows
param(
    [Parameter()]
    [ValidateSet("build", "up", "down", "logs", "shell", "test-token", "sync-repo", "run-host")]
    [string]$Command = "up"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Require-Env {
    if (-not (Test-Path "$ProjectRoot\.env")) {
        Copy-Item "$ProjectRoot\.env.example" "$ProjectRoot\.env"
        Write-Host "Created .env from example. Please edit it with the real token." -ForegroundColor Yellow
        exit 1
    }
}

switch ($Command) {
    "build" {
        docker compose -f "$ProjectRoot\docker-compose.yml" build
    }
    "up" {
        Require-Env
        docker compose -f "$ProjectRoot\docker-compose.yml" up -d --build
        Write-Host "Bot is running in Docker. Logs: .\scripts\dev.ps1 logs" -ForegroundColor Green
    }
    "down" {
        docker compose -f "$ProjectRoot\docker-compose.yml" down
    }
    "logs" {
        docker compose -f "$ProjectRoot\docker-compose.yml" logs -f bot
    }
    "shell" {
        docker compose -f "$ProjectRoot\docker-compose.yml" exec bot bash
    }
    "test-token" {
        Require-Env
        docker run --rm --env-file "$ProjectRoot\.env" erik-liminal-calendar-bot python -c "import asyncio, os; from telegram import Bot; print(asyncio.run(Bot(os.environ['ERIK_BOT_TOKEN']).get_me()).username)"
    }
    "sync-repo" {
        Require-Env
        docker compose -f "$ProjectRoot\docker-compose.yml" run --rm bot python scripts/sync_repo.py
    }
    "run-host" {
        Require-Env
        Set-Location $ProjectRoot
        python bot.py
    }
    default {
        Write-Host "Usage: .\scripts\dev.ps1 [build|up|down|logs|shell|test-token|sync-repo|run-host]"
    }
}
