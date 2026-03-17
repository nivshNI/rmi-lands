"""
Core monitor — fetches tenders from RMI API, detects new entries.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from config import Config
from rmi_scraper import fetch_tenders, tender_key

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


def diff_snapshots(old: Snapshot, new: Snapshot) -> dict:
    new_ids = new.tender_ids - old.tender_ids
    removed_ids = old.tender_ids - new.tender_ids

    added = [t for t in new.tenders if tender_key(t) in new_ids]
    removed_ids_list = list(removed_ids)

    return {
        "added": added,
        "removed_ids": removed_ids_list,
        "total_before": len(old.tender_ids),
        "total_after": len(new.tender_ids),
    }
