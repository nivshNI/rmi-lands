#!/usr/bin/env python3
"""
Render the current tender snapshot as an interactive map at docs/index.html.

Run standalone (python build_map.py) or let main.py call build_map() after
every check, so the map always reflects the latest baseline.
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path

from geocode import locate
from watchlist import load_watchlist

logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent
BASELINE_FILE = ROOT / "baseline.json"
OUTPUT_FILE = ROOT / "docs" / "index.html"
TEMPLATE_FILE = ROOT / "map_template.html"

# Used to link the map's "sync stars" helper straight to the file to edit.
REPO_SLUG = os.getenv("RMI_REPO_SLUG", "nivshni/rmi-lands")
REPO_BRANCH = os.getenv("RMI_REPO_BRANCH", "main")

# Categorical palette, ordered by tender-type frequency. Both modes were
# validated all-pairs (map markers are scatter-like, so any two can end up
# side by side): light worst CVD ΔE 9.9 / normal 21.8, dark 8.5 / 18.1.
TYPE_COLORS_LIGHT = [
    "#dd9d23", "#5c821e", "#3a1fec", "#9568c8", "#ff4b7a", "#05b7e0", "#a31441",
]
TYPE_COLORS_DARK = [
    "#bb8526", "#54700b", "#5a55cd", "#bc53ff", "#993a5d", "#2e9bc9", "#eb5487",
]

# Fixed slot order — a type keeps its color no matter which filters are on.
TYPE_ORDER = [
    "מכרז פומבי רגיל",
    "הרשמה והגרלה",
    "מחיר מטרה",
    "מכרז ייזום",
    "דיור להשכרה",
    "מכרזי עמידר",
    "מכרז למגרש בלתי מסוים",
]

PRECISION_LABELS = {
    "exact": "מיקום היישוב",
    "approx": "מיקום מקורב",
    "region": "מרכז המרחב בלבד",
}

TENDER_URL = "https://apps.land.gov.il/MichrazimSite/#/michraz/{id}"


def _spread(points: list[dict]) -> None:
    """
    Fan out tenders sharing one coordinate so every marker stays clickable
    instead of hiding under the one on top.
    """
    groups: dict[tuple, list[dict]] = {}
    for p in points:
        groups.setdefault((round(p["lat"], 5), round(p["lon"], 5)), []).append(p)

    for group in groups.values():
        if len(group) == 1:
            continue
        # ~90 m radius, growing slowly so even 20+ tenders stay near the town
        radius = 0.0008 * (1 + len(group) / 25)
        for i, p in enumerate(group):
            angle = 2 * math.pi * i / len(group)
            p["lat"] += radius * math.cos(angle)
            p["lon"] += radius * math.sin(angle) / math.cos(math.radians(p["lat"]))


def collect_points(tenders: list[dict]) -> list[dict]:
    points, unlocated = [], 0

    for t in tenders:
        loc = locate(t.get("settlement", ""), t.get("region", ""))
        if loc is None:
            unlocated += 1
            continue

        try:
            slot = TYPE_ORDER.index(t.get("type", ""))
        except ValueError:
            slot = len(TYPE_ORDER) - 1

        points.append({
            "lat": loc["lat"],
            "lon": loc["lon"],
            "precision": loc["precision"],
            "precision_label": PRECISION_LABELS[loc["precision"]],
            "slot": slot,
            "id": t.get("id"),
            "url": TENDER_URL.format(id=t.get("id")),
            "number": t.get("number", ""),
            "type": t.get("type", ""),
            "region": t.get("region", ""),
            "settlement": t.get("settlement", ""),
            "neighborhood": t.get("neighborhood", ""),
            "purpose": t.get("purpose", ""),
            "units": t.get("units", 0),
            "online": bool(t.get("online")),
            "booklet": bool(t.get("published_booklet")),
            "pub_date": t.get("pub_date", ""),
            "open_date": t.get("open_date", ""),
            "close_date": t.get("close_date", ""),
        })

    if unlocated:
        logger.warning("%d tenders could not be placed on the map", unlocated)

    _spread(points)
    return points


def build_map(baseline_file: Path = BASELINE_FILE, output_file: Path = OUTPUT_FILE) -> Path:
    """Read the snapshot, render the map, return the written path."""
    data = json.loads(baseline_file.read_text(encoding="utf-8"))
    tenders = data.get("tenders", [])
    points = collect_points(tenders)

    types_present = sorted({p["slot"] for p in points})
    legend = [
        {
            "slot": slot,
            "name": TYPE_ORDER[slot],
            "light": TYPE_COLORS_LIGHT[slot],
            "dark": TYPE_COLORS_DARK[slot],
            "count": sum(1 for p in points if p["slot"] == slot),
        }
        for slot in types_present
    ]

    purpose_counts: dict[str, int] = {}
    for p in points:
        purpose_counts[p["purpose"] or "—"] = purpose_counts.get(p["purpose"] or "—", 0) + 1
    purposes = [
        {"name": name, "count": count}
        for name, count in sorted(purpose_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    payload = {
        "generated": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
        "total": len(tenders),
        "plotted": len(points),
        "legend": legend,
        "purposes": purposes,
        "watchlist": sorted(load_watchlist()),
        "watchlistEditUrl": f"https://github.com/{REPO_SLUG}/edit/{REPO_BRANCH}/watchlist.json",
        "points": points,
    }

    html = TEMPLATE_FILE.read_text(encoding="utf-8").replace(
        "__TENDER_DATA__", json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding="utf-8")
    logger.info("Map written to %s (%d/%d tenders plotted)", output_file, len(points), len(tenders))
    return output_file


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
    build_map()
