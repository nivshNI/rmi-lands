"""
Core monitor — fetches tenders from RMI API, detects new entries.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from config import Config
from rmi_scraper import fetch_tenders, tender_key
from watchlist import diff_tender

logger = logging.getLogger(__name__)


@dataclass
class Snapshot:
    tenders: list[dict] = field(default_factory=list)
    tender_ids: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.tenders and not self.tender_ids:
            self.tender_ids = {tender_key(t) for t in self.tenders}


def take_snapshot() -> Snapshot:
    tenders = fetch_tenders(uchlusiya_codes=Config.RMI_UCHLUSIYA)
    return Snapshot(tenders=tenders)


def diff_snapshots(old: Snapshot, new: Snapshot, watched_ids: set[str] | None = None) -> dict:
    new_ids = new.tender_ids - old.tender_ids
    removed_ids = old.tender_ids - new.tender_ids

    added = [t for t in new.tenders if tender_key(t) in new_ids]
    removed_ids_list = list(removed_ids)

    return {
        "added": added,
        "removed_ids": removed_ids_list,
        "updated": _updated_watched(old, new, watched_ids or set()),
        "watched_removed": [i for i in removed_ids_list if i in (watched_ids or set())],
        "total_before": len(old.tender_ids),
        "total_after": len(new.tender_ids),
    }


def _updated_watched(old: Snapshot, new: Snapshot, watched_ids: set[str]) -> list[dict]:
    """Field-level changes on starred tenders that exist in both snapshots."""
    if not watched_ids:
        return []

    old_by_id = {tender_key(t): t for t in old.tenders}
    updates = []

    for tender in new.tenders:
        key = tender_key(tender)
        if key not in watched_ids:
            continue
        previous = old_by_id.get(key)
        if previous is None:
            continue
        changes = diff_tender(previous, tender)
        if changes:
            updates.append({"tender": tender, "changes": changes})

    return updates
