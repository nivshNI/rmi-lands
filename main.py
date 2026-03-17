#!/usr/bin/env python3
"""
RMI Lands — Monitor Israel Land Authority tenders and get notified about new ones.

Usage:
    python main.py              # run once (good for cron / GitHub Actions)
    python main.py --loop       # run continuously with built-in polling
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from config import Config
from monitor import Snapshot, diff_snapshots, take_snapshot
from notifier import notify
from rmi_scraper import tender_key
from summarizer import build_notification

SNAPSHOT_FILE = Path(__file__).parent / ".last_snapshot.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("rmi_lands")


def load_previous_snapshot() -> Optional[Snapshot]:
    if not SNAPSHOT_FILE.exists():
        return None
    try:
        data = json.loads(SNAPSHOT_FILE.read_text())
        tenders = data.get("tenders", [])
        return Snapshot(tenders=tenders)
    except (json.JSONDecodeError, KeyError):
        logger.warning("Corrupted snapshot file, treating as first run")
        return None


def save_snapshot(snap: Snapshot) -> None:
    data = {"tenders": snap.tenders}
    SNAPSHOT_FILE.write_text(json.dumps(data, ensure_ascii=False))


def check_once() -> bool:
    logger.info("Checking RMI tenders (filter: Uchlusiya=%s)...", Config.RMI_UCHLUSIYA)
    try:
        current = take_snapshot()
    except Exception as e:
        logger.exception("Failed to fetch tenders")
        notify(
            title="RMI Lands — שגיאה!",
            message=f"הבדיקה נכשלה:\n{e}",
        )
        return False

    previous = load_previous_snapshot()
    save_snapshot(current)

    if previous is None:
        logger.info("First run — baseline saved (%d tenders).", len(current.tenders))
        return False

    changes = diff_snapshots(previous, current)

    if not changes["added"] and not changes["removed_ids"]:
        logger.info("No new tenders. Total: %d", len(current.tenders))
        return False

    logger.info(
        "Changes detected! new=%d  removed=%d  total=%d",
        len(changes["added"]), len(changes["removed_ids"]), len(current.tenders),
    )

    if changes["added"]:
        title, plain, html = build_notification(
            added=changes["added"],
            removed_ids=changes["removed_ids"],
            total_before=changes["total_before"],
            total_after=changes["total_after"],
        )
        notify(title=title, message=plain, html_message=html)

    return True


def run_loop() -> None:
    interval_hrs = Config.POLL_INTERVAL / 3600
    logger.info("Starting continuous monitor (every %.1f hours)...", interval_hrs)
    while True:
        try:
            check_once()
        except KeyboardInterrupt:
            logger.info("Shutting down.")
            sys.exit(0)
        except Exception:
            logger.exception("Unexpected error in poll loop")
        time.sleep(Config.POLL_INTERVAL)


def main() -> None:
    parser = argparse.ArgumentParser(description="RMI Lands — Tender Monitor")
    parser.add_argument("--loop", action="store_true", help="Run continuously instead of once")
    args = parser.parse_args()

    if args.loop:
        run_loop()
    else:
        check_once()


if __name__ == "__main__":
    main()
