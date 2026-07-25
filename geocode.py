"""
Resolve RMI settlement names to map coordinates.

Three resolution tiers, reported per tender so the map can be honest about
how precise each marker is:

    "exact"   — matched a settlement point in geo/settlements.json
    "approx"  — matched a curated override (regional councils, alternate spellings)
    "region"  — no settlement match; fell back to the RMI region centroid
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_SETTLEMENTS_FILE = Path(__file__).parent / "geo" / "settlements.json"

# Centroids of the RMI administrative regions (KodMerchav), used as a last
# resort so a tender never silently disappears from the map.
REGION_CENTROIDS: dict[str, tuple[float, float]] = {
    "ירושלים": (31.7683, 35.2137),
    "צפון": (32.8000, 35.3000),
    "חיפה": (32.7940, 34.9896),
    "מרכז": (32.0000, 34.9000),
    "תל אביב": (32.0853, 34.7818),
    "דרום": (31.2000, 34.8000),
    'יו"ש': (32.0000, 35.2500),
    "עזה": (31.5000, 34.4667),
    "מטה הרשות": (31.7683, 35.2137),
}

# Settlements absent from the bundled dataset. Regional councils ("מ.א.") have
# no single point by nature — these are council-area centres, not addresses,
# hence the "approx" tier.
MANUAL_COORDS: dict[str, tuple[float, float]] = {
    # Regional councils — area centres
    "מ.א. אשכול": (31.3000, 34.4667),
    "מ.א. באר טוביה": (31.7333, 34.7333),
    "מ.א. בני שמעון": (31.3167, 34.8500),
    "מ.א. גולן": (32.9000, 35.7500),
    "מ.א. דרום שרון": (32.1500, 34.9333),
    "מ.א. הערבה התיכונה": (30.6667, 35.1667),
    "מ.א. חבל יבנה": (31.8167, 34.7167),
    "מ.א. יואב": (31.6500, 34.8000),
    "מ.א. משגב": (32.8833, 35.2833),
    "מ.א. ערבות ירדן": (32.0000, 35.4500),
    "מ.א. רמת נגב": (30.8667, 34.8000),
    "מ.א. תמר": (31.0500, 35.3833),
    "מ.מ.ת. נאות חובב": (31.1333, 34.8000),
    # Towns and localities missing from the dataset
    "אדם - גבע בנימין": (31.8342, 35.2725),
    "אפרת": (31.6547, 35.1508),
    "באר גנים": (31.6706, 34.5811),
    "בית אל": (31.9422, 35.2225),
    "בית אריה-עופרים": (32.0356, 35.0492),
    "בית ג'אן": (32.9647, 35.3767),
    "בנימינה-ג.עדה": (32.5164, 34.9486),
    "ג'וליס": (32.9314, 35.1719),
    "גוש חלב (ג'ש)": (33.0244, 35.4467),
    "חריש": (32.4614, 35.0489),
    "יאנוח-ג'ת": (32.9836, 35.2472),
    "יהוד-מונוסון": (32.0333, 34.8833),
    "יקנעם עלית": (32.6572, 35.1103),
    "מפעלי מישור רותם": (31.0333, 35.1000),
    "משמר אילון": (31.8500, 34.9667),
    "נוה דניאל": (31.6800, 35.1400),
    "נוף הגליל": (32.7100, 35.3200),
    "נצנה": (30.8833, 34.4167),
    "סחנין": (32.8644, 35.2975),
    "פורייה-כפר עבודה": (32.7550, 35.5300),
    "פרדיס": (32.5833, 34.9667),
    "קציר": (32.4833, 35.1000),
    "רחלים": (32.1000, 35.2667),
    "שבלי-אום ג'נם": (32.7000, 35.4000),
    "תל ציון": (31.9300, 35.2500),
    "ברקן(בית אב\"א": (32.1067, 35.0672),
}

_lookup: dict[str, tuple[float, float]] = {}


def _normalize(name: str) -> str:
    """Fold spelling variants so 'יהוד-מונוסון' and 'יהוד מונוסון' match."""
    s = name.strip().replace('"', "").replace("״", "").replace("׳", "")
    s = s.replace("-", " ").replace("–", " ")
    s = re.sub(r"\([^)]*\)", "", s)
    s = s.replace("(", "").replace(")", "")
    return re.sub(r"\s+", " ", s).strip()


def _ensure_lookup() -> None:
    global _lookup
    if _lookup:
        return

    try:
        raw = json.loads(_SETTLEMENTS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.exception("Could not read %s — falling back to region centroids", _SETTLEMENTS_FILE)
        raw = {}

    for name, (lat, lon) in raw.items():
        _lookup.setdefault(_normalize(name), (lat, lon))

    logger.info("Loaded %d settlement coordinates", len(_lookup))


def locate(settlement: str, region: str) -> Optional[dict]:
    """
    Return {"lat", "lon", "precision"} for a tender, or None if even the
    region is unknown.
    """
    _ensure_lookup()

    key = _normalize(settlement)

    if key in _lookup:
        lat, lon = _lookup[key]
        return {"lat": lat, "lon": lon, "precision": "exact"}

    for manual_name, coords in MANUAL_COORDS.items():
        if _normalize(manual_name) == key:
            return {"lat": coords[0], "lon": coords[1], "precision": "approx"}

    centroid = REGION_CENTROIDS.get(region.strip())
    if centroid:
        return {"lat": centroid[0], "lon": centroid[1], "precision": "region"}

    return None
