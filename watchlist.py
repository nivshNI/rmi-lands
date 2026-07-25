"""
Watchlist — tenders you starred and want change alerts for.

watchlist.json is the source of truth the monitor reads. The map page can
toggle stars locally (browser storage) and hands you the JSON to commit here,
since a static page has no way to write back to the repository.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

WATCHLIST_FILE = Path(__file__).parent / "watchlist.json"

# Fields worth alerting on, with the label used in the notification.
WATCHED_FIELDS: dict[str, str] = {
    "open_date": "מועד פתיחת המכרז",
    "close_date": "מועד אחרון להגשה",
    "committee_date": "מועד ועדה",
    "pub_date": "תאריך פרסום",
    "published_booklet": "פרסום חוברת",
    "online": "מכרז מקוון",
    "units": 'יחידות דיור',
    "purpose": "ייעוד",
    "type": "סוג המכרז",
    "settlement": "יישוב",
    "neighborhood": "שכונה",
}


def load_watchlist() -> set[str]:
    """Return the set of starred tender IDs (as strings)."""
    if not WATCHLIST_FILE.exists():
        return set()
    try:
        data = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("watchlist.json is not valid JSON — treating as empty")
        return set()

    ids = data.get("ids", data) if isinstance(data, dict) else data
    if not isinstance(ids, list):
        logger.warning("watchlist.json has an unexpected shape — treating as empty")
        return set()
    return {str(i) for i in ids}


def save_watchlist(ids: set[str]) -> None:
    WATCHLIST_FILE.write_text(
        json.dumps({"ids": sorted(ids, key=str)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _display(field: str, value) -> str:
    if field in ("published_booklet", "online"):
        return "כן" if value else "לא"
    return str(value) if value not in (None, "") else "—"


def diff_tender(old: dict, new: dict) -> list[dict]:
    """Field-level changes between two versions of the same tender."""
    changes = []
    for field, label in WATCHED_FIELDS.items():
        before, after = old.get(field), new.get(field)
        if before != after:
            changes.append({
                "field": field,
                "label": label,
                "before": _display(field, before),
                "after": _display(field, after),
            })
    return changes
