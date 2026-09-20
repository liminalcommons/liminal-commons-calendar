#!/usr/bin/env python3
"""Erik's vibecoding gateway for the Liminal Commons calendar.

This is NOT a finished calendar bot. It is a Telegram interface that lets Erik
send coding prompts, which are dispatched to local AI coding agents
(Hermes, Claude Code, OpenCode) that edit the calendar repo.
"""
import asyncio
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.environ.get("ERIK_BOT_TOKEN")
REPO_ROOT = Path(__file__).resolve().parent
STATE_DIR = REPO_ROOT / "data"
STATE_DB = STATE_DIR / "gateway.db"
AGENT_LOG_DIR = STATE_DIR / "agent_logs"

AGENTS = {
    "hermes": {
        "label": "Hermes",
        "cmd": ["hermes", "chat", "-q", "{prompt}"],
        "timeout": 600,
    },
    "claude": {
        "label": "Claude Code",
        "cmd": ["claude", "-p", "{prompt}", "--allowedTools", "Read,Edit,Bash,Write", "--max-turns", "20"],
        "timeout": 600,
    },
    "opencode": {
        "label": "OpenCode",
        "cmd": ["opencode", "run", "{prompt}"],
        "timeout": 600,
    },
}

DEFAULT_AGENT = "claude"


def init_db() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    AGENT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(STATE_DB) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER,
                username TEXT,
                role TEXT NOT NULL,
                text TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                agent TEXT NOT NULL,
                prompt TEXT NOT NULL,
                status TEXT NOT NULL,
                log_file TEXT,
                pid INTEGER,
                created_at TEXT NOT NULL,
                finished_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
            CREATE INDEX IF NOT EXISTS idx_runs_chat ON agent_runs(chat_id);
            """
        )


def log_message(chat_id: int, user_id: Optional[int], username: Optional[str], role: str, text: str) -> None:
    with sqlite3.connect(STATE_DB) as conn:
        conn.execute(
            "INSERT INTO messages (chat_id, user_id, username, role, text, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (chat_id, user_id, username, role, text, datetime.now(timezone.utc).isoformat()),
        )


def log_run(chat_id: int, agent: str, prompt: str, log_file: Path, pid: int) -> int:
    with sqlite3.connect(STATE_DB) as conn:
        cur = conn.execute(
            "INSERT INTO agent_runs (chat_id, agent, prompt, status, log_file, pid, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (chat_id, agent, prompt, "running", str(log_file), pid, datetime.now(timezone.utc).isoformat()),
        )
        return cur.lastrowid


def update_run(run_id: int, status: str) -> None:
    with sqlite3.connect(STATE_DB) as conn:
        conn.execute(
            "UPDATE agent_runs SET status = ?, finished_at = ? WHERE id = ?",
            (status, datetime.now(timezone.utc).isoformat(), run_id),
        )


def get_running_runs(chat_id: Optional[int] = None) -> list[dict]:
    with sqlite3.connect(STATE_DB) as conn:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM agent_runs WHERE status = 'running'"
        params = ()
        if chat_id is not None:
            sql += " AND chat_id = ?"
            params = (chat_id,)
        sql += " ORDER BY created_at DESC"
        return [dict(row) for row in conn.execute(sql, params)]


def format_run(run: dict) -> str:
    prompt = run["prompt"]
    if len(prompt) > 80:
        prompt = prompt[:77] + "..."
    return f"#{run['id']} {run['agent']}: {prompt}"


def is_agent_request(text: str) -> tuple[bool, str, str]:
    """Detect '@agent prompt' shorthand. Returns (matched, agent, prompt)."""
    match = re.match(r"^@(\w+)\s+(.*)$", text.strip(), re.DOTALL)
    if match:
        agent = match.group(1).lower()
        prompt = match.group(2).strip()
        if agent in AGENTS:
            return True, agent, prompt
    return False, "", ""


def sanitize_filename(text: str) -> str:
    return re.sub(r"[^\w\-]+", "_", text.strip())[:50] or "run"


def spawn_agent(chat_id: int, agent: str, prompt: str) -> tuple[int, Path]:
    agent_cfg = AGENTS[agent]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_file = AGENT_LOG_DIR / f"{agent}_{timestamp}_{sanitize_filename(prompt)}.log"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"Agent: {agent_cfg['label']}\nPrompt: {prompt}\nStarted: {datetime.now(timezone.utc).isoformat()}\n{'='*60}\n")

    cmd = [part.format(prompt=prompt) for part in agent_cfg["cmd"]]
    proc = subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        stdout=open(log_file, "a", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc.pid, log_file


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Hi Erik. This is your vibecoding gateway for the Liminal Commons calendar.\n\n"
        "I am not a finished bot — I connect you to coding agents that edit the repo.\n\n"
        "Commands:\n"
        "/claude <prompt> — run Claude Code\n"
        "/opencode <prompt> — run OpenCode\n"
        "/hermes <prompt> — run Hermes Agent\n"
        "/status — show running agents\n"
        "/cancel <id> — stop an agent\n"
        "/history — last messages\n\n"
        "Shorthand:\n"
        "@claude add an event list command\n"
        "@opencode write tests for the calendar"
    )
    await update.message.reply_text(text)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def dispatch_agent(update: Update, context: ContextTypes.DEFAULT_TYPE, agent: str) -> None:
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text(f"Usage: /{agent} <coding prompt>")
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id if update.effective_user else None
    username = update.effective_user.username if update.effective_user else None

    log_message(chat_id, user_id, username, "user", f"/{agent} {prompt}")
    status_msg = await update.message.reply_text(f"Starting {AGENTS[agent]['label']}...")

    try:
        pid, log_file = spawn_agent(chat_id, agent, prompt)
        run_id = log_run(chat_id, agent, prompt, log_file, pid)
        await status_msg.edit_text(f"#{run_id} {AGENTS[agent]['label']} started. Use /status to check.")

        # Fire-and-forollow monitor
        asyncio.create_task(monitor_agent(run_id, pid, log_file, chat_id, context))
    except Exception as e:
        await status_msg.edit_text(f"Failed to start {agent}: {e}")


def is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def terminate_process(pid: int) -> None:
    """Cross-platform gentle termination."""
    try:
        if sys.platform == "win32":
            os.kill(pid, signal.CTRL_BREAK_EVENT)
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception:
        pass


async def monitor_agent(run_id: int, pid: int, log_file: Path, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Poll the agent process and send a summary when it finishes."""
    agent_cfg = AGENTS.get(DEFAULT_AGENT, AGENTS["claude"])
    timeout = agent_cfg["timeout"]
    start = time.time()
    try:
        while is_process_alive(pid):
            await asyncio.sleep(2)
            if time.time() - start > timeout:
                terminate_process(pid)
                update_run(run_id, "timeout")
                await context.bot.send_message(chat_id, f"#{run_id} timed out.")
                return
    except Exception as e:
        update_run(run_id, f"error: {e}")
        await context.bot.send_message(chat_id, f"#{run_id} monitor error: {e}")
        return

    update_run(run_id, "done")
    summary = summarize_log(log_file)
    try:
        await context.bot.send_message(chat_id, f"#{run_id} finished.\n\n{summary}")
    except Exception:
        await context.bot.send_message(chat_id, f"#{run_id} finished. Log: {log_file}")


def summarize_log(log_file: Path, max_chars: int = 3500) -> str:
    if not log_file.exists():
        return "No log file."
    text = log_file.read_text(encoding="utf-8", errors="ignore")
    # Tail is usually most useful
    tail = text[-max_chars:] if len(text) > max_chars else text
    return f"```\n{tail}\n```"


async def claude_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await dispatch_agent(update, context, "claude")


async def opencode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await dispatch_agent(update, context, "opencode")


async def hermes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await dispatch_agent(update, context, "hermes")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    runs = get_running_runs(chat_id)
    if not runs:
        await update.message.reply_text("No agents running.")
        return
    text = "Running agents:\n\n" + "\n".join(format_run(r) for r in runs)
    await update.message.reply_text(text)


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /cancel <run_id>")
        return
    try:
        run_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Run ID must be a number.")
        return

    with sqlite3.connect(STATE_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        await update.message.reply_text(f"No run #{run_id}.")
        return

    pid = row["pid"]
    try:
        terminate_process(pid)
        update_run(run_id, "cancelled")
        await update.message.reply_text(f"Cancelled run #{run_id}.")
    except ProcessLookupError:
        update_run(run_id, "done")
        await update.message.reply_text(f"Run #{run_id} was already done.")
    except Exception as e:
        await update.message.reply_text(f"Could not cancel run #{run_id}: {e}")


async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    with sqlite3.connect(STATE_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT role, text, created_at FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT 20",
            (chat_id,),
        ).fetchall()
    if not rows:
        await update.message.reply_text("No history yet.")
        return
    lines = []
    for row in rows:
        t = row["created_at"][:16] if row["created_at"] else "?"
        lines.append(f"[{t}] {row['role']}: {row['text'][:120]}")
    await update.message.reply_text("\n".join(reversed(lines)))


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id if update.effective_user else None
    username = update.effective_user.username if update.effective_user else None

    log_message(chat_id, user_id, username, "user", text)

    matched, agent, prompt = is_agent_request(text)
    if matched:
        # Re-use context.args style dispatch
        context.args = prompt.split()
        await dispatch_agent(update, context, agent)
        return

    await update.message.reply_text(
        "I pass your prompts to coding agents. Try:\n"
        "@claude <prompt>\n"
        "@opencode <prompt>\n"
        "or /help for commands."
    )


def main() -> None:
    if not TOKEN:
        raise SystemExit("Set ERIK_BOT_TOKEN env var.")
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("claude", claude_cmd))
    app.add_handler(CommandHandler("opencode", opencode_cmd))
    app.add_handler(CommandHandler("hermes", hermes_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    print("Vibecoding gateway polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
