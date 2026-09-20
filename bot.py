import os
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("ERIK_BOT_TOKEN")
DATA_FILE = Path(__file__).with_name("events.json")
SYNC_SCRIPT = Path(__file__).with_name("scripts") / "sync_repo.py"

TITLE, WHEN, WHERE, DESC, DELETE_CONFIRM = range(5)


def load_events() -> dict:
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_events(events: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)


def sync_repo() -> None:
    """Push/pull events.json with GitHub if configured."""
    if not os.environ.get("GITHUB_TOKEN") or not SYNC_SCRIPT.exists():
        return
    try:
        subprocess.run([sys.executable, str(SYNC_SCRIPT)], check=True, capture_output=True, timeout=60)
    except Exception as e:
        print(f"Sync warning: {e}")


def next_event_id(events: dict) -> int:
    ids = [int(k) for k in events.keys() if k.isdigit()]
    return max(ids, default=0) + 1


def format_event(eid: str, event: dict) -> str:
    lines = [
        f"<b>#{eid}</b>: {event.get('title', 'Untitled')}",
        f"🗓 {event.get('when', 'TBD')}",
    ]
    if event.get("where"):
        lines.append(f"📍 {event['where']}")
    if event.get("description"):
        lines.append(f"📝 {event['description']}")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        "Hi Erik. I keep the Liminal Commons calendar.\n\n"
        "/events — list upcoming\n"
        "/add — add an event\n"
        "/delete <id> — remove an event"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        "<b>Liminal Commons Calendar Bot</b>\n\n"
        "/events — list all events\n"
        "/add — start adding an event\n"
        "/delete <id> — delete event #id\n"
        "/cancel — cancel what you're doing"
    )


async def events_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    events = load_events()
    if not events:
        await update.message.reply_text("No events yet. Add one with /add")
        return
    text = "\n\n".join(format_event(eid, ev) for eid, ev in sorted(events.items(), key=lambda x: int(x[0])))
    await update.message.reply_html(text)


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Event title?")
    return TITLE


async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["event"] = {"title": update.message.text.strip()}
    await update.message.reply_text("When? (free text, e.g. 'Oct 12, 20:00 UTC')")
    return WHEN


async def add_when(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["event"]["when"] = update.message.text.strip()
    await update.message.reply_text("Where? (or '-' to skip)")
    return WHERE


async def add_where(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    context.user_data["event"]["where"] = "" if text == "-" else text
    await update.message.reply_text("Description? (or '-' to skip)")
    return DESC


async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    event = context.user_data["event"]
    event["description"] = "" if text == "-" else text
    event["created"] = datetime.now(timezone.utc).isoformat()

    events = load_events()
    eid = str(next_event_id(events))
    events[eid] = event
    save_events(events)
    sync_repo()

    await update.message.reply_html(f"Saved event #{eid}:\n\n{format_event(eid, event)}")
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /delete <id>")
        return
    eid = context.args[0]
    events = load_events()
    if eid not in events:
        await update.message.reply_text(f"No event #{eid}.")
        return
    del events[eid]
    save_events(events)
    sync_repo()
    await update.message.reply_text(f"Deleted event #{eid}.")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("I didn't understand that. Try /help.")


def main() -> None:
    if not TOKEN:
        raise SystemExit("Set ERIK_BOT_TOKEN env var.")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("events", events_cmd))
    app.add_handler(CommandHandler("delete", delete_cmd))

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            WHEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_when)],
            WHERE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_where)],
            DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(add_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    print("Bot polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
