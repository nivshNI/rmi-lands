"""
Direct API scraper for Israel Land Authority (RMI) tenders site.

Calls the REST API at apps.land.gov.il/MichrazimSite/api — no browser needed.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://apps.land.gov.il/MichrazimSite/api"
_YESHUV_CACHE_FILE = Path(__file__).parent / ".yeshuv_cache.json"

REGION_NAMES = {
    0: "מטה הרשות", 1: "ירושלים", 2: "צפון", 3: "חיפה",
    4: "מרכז", 5: "תל אביב", 6: "דרום", 7: 'יו"ש', 8: "עזה",
}

TENDER_TYPE_NAMES = {
    1: "מכרז פומבי רגיל", 2: "הרשמה והגרלה", 3: "מכרז למגרש בלתי מסוים",
    4: "קדימות על פי עדיפות", 5: "מחיר מטרה", 6: "דיור להשכרה",
    7: "מחיר למשתכן", 8: "דיור במחיר מופחת", 9: "מכרז ייזום",
    10: "מכרזי עמידר", 11: "מכרזי החברה לפיתוח עכו",
}

PURPOSE_NAMES = {
    1: "בנייה נמוכה/צמודת קרקע", 2: "בנייה רוויה", 3: "מסחר ו/או משרדים",
    4: "תעשיה", 5: "מוסדות ו/או בניינים ציבוריים", 6: "חניונים",
    7: "תחנות דלק", 8: "מלונאות", 9: "ספורט/נופש/תיירות/מלונאות",
    10: "כרייה וחציבה", 11: "חקלאות", 12: "מגורים/מסחר/מלונאות/נופש",
    13: "דיור מוגן", 14: "נכסי הרשות - מכירה - מגורים",
    15: "נכסי הרשות - מכירה - אחר", 16: "עודפים", 17: "נופש וחקלאות",
    18: "הטמנת פסולת", 20: "דיור להשכרה", 23: "אנרגיה מתחדשת",
    24: "תחנת כוח", 26: "תעסוקה", 99: "אחר",
}

_yeshuv_cache: dict = {}


def _ensure_yeshuv_cache() -> None:
    global _yeshuv_cache
    if _yeshuv_cache:
        return

    if _YESHUV_CACHE_FILE.exists():
        try:
            _yeshuv_cache = {int(k): v for k, v in json.loads(_YESHUV_CACHE_FILE.read_text()).items()}
            logger.info("Loaded %d settlement names from disk cache", len(_yeshuv_cache))
            return
        except Exception:
            pass

    try:
        resp = httpx.get(f"{BASE_URL}/YeshuvimApi/Get", timeout=60)
        resp.raise_for_status()
        for item in resp.json():
            code = item.get("mtysvSemelYishuv")
            name = item.get("mtysvShemYishuv", "").strip()
            if code is not None and name:
                _yeshuv_cache[code] = name
        _YESHUV_CACHE_FILE.write_text(json.dumps(_yeshuv_cache, ensure_ascii=False))
        logger.info("Loaded %d settlement names from API (cached to disk)", len(_yeshuv_cache))
    except Exception:
        logger.exception("Failed to load settlement names")


def _format_date(iso_str: Optional[str]) -> str:
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return iso_str


def fetch_tenders(uchlusiya_codes: Optional[list] = None) -> list:
    """
    Call the RMI search API and return enriched tender dicts.

    uchlusiya_codes: population priority filter codes, e.g. [1] for "אנשים עם מוגבלות".
    """
    _ensure_yeshuv_cache()

    payload: dict = {"ActiveQuickSearch": False, "ActiveMichraz": True}
    if uchlusiya_codes:
        payload["Uchlusiya"] = uchlusiya_codes

    logger.info("Searching RMI tenders with payload: %s", payload)
    resp = httpx.post(f"{BASE_URL}/SearchApi/Search", json=payload, timeout=60)
    resp.raise_for_status()
    raw_tenders = resp.json()
    logger.info("Got %d raw tenders from API", len(raw_tenders))

    return [_enrich(t) for t in raw_tenders]


def _enrich(raw: dict) -> dict:
    """Convert raw API tender to a human-readable dict."""
    michraz_id = raw.get("MichrazID", 0)
    return {
        "id": michraz_id,
        "number": raw.get("MichrazName", ""),
        "type": TENDER_TYPE_NAMES.get(raw.get("KodSugMichraz", -1), ""),
        "region": REGION_NAMES.get(raw.get("KodMerchav", -1), ""),
        "settlement": _yeshuv_cache.get(raw.get("KodYeshuv", -1), ""),
        "neighborhood": (raw.get("Shchuna") or "").strip(),
        "purpose": PURPOSE_NAMES.get(raw.get("KodYeudMichraz", -1), ""),
        "units": raw.get("YechidotDiur", 0),
        "published_booklet": raw.get("PublishedChoveret", False),
        "online": raw.get("Mekuvan", False),
        "pub_date": _format_date(raw.get("PirsumDate")),
        "open_date": _format_date(raw.get("PtichaDate")),
        "close_date": _format_date(raw.get("SgiraDate")),
        "committee_date": _format_date(raw.get("VaadaDate")),
    }


def tender_key(tender: dict) -> str:
    """Unique identifier used for change detection."""
    return str(tender["id"])


def format_tender_text(tender: dict) -> str:
    """Human-readable text representation for notifications."""
    booklet = "פורסמה חוברת" if tender["published_booklet"] else "טרם פורסמה חוברת"
    location = tender["settlement"]
    if tender["neighborhood"]:
        location += f', {tender["neighborhood"]}'

    lines = [
        f'מכרז {tender["number"]} | {tender["type"]} | {tender["units"]} יח"ד',
        f'  מרחב: {tender["region"]}',
        f'  יישוב: {location}',
        f'  ייעוד: {tender["purpose"]}',
        f'  תאריך פרסום: {tender["pub_date"]}',
        f"  {booklet}",
    ]
    if tender["close_date"]:
        lines.append(f'  מועד אחרון: {tender["close_date"]}')
    return "\n".join(lines)
