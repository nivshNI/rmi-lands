"""
Build notification content for new tender alerts.
"""

import logging

from rmi_scraper import format_tender_text

logger = logging.getLogger(__name__)


def build_notification(added: list[dict], removed_ids: list[str],
                       total_before: int, total_after: int) -> tuple[str, str, str]:
    """
    Returns (title, plain_text, html_text) for a notification about new tenders.
    """
    title = f"מכרזי קרקע — {len(added)} מכרזים חדשים!"

    # Plain text version
    lines = [f"נמצאו {len(added)} מכרזים חדשים (סה\"כ: {total_after})", ""]
    for t in added:
        lines.append(format_tender_text(t))
        lines.append("")

    if removed_ids:
        lines.append(f"הוסרו {len(removed_ids)} מכרזים.")
    plain = "\n".join(lines)

    # HTML version for email
    html = _build_html(added, removed_ids, total_before, total_after)

    return title, plain, html


def _build_html(added: list[dict], removed_ids: list[str],
                total_before: int, total_after: int) -> str:
    rows = ""
    for t in added:
        booklet = "&#10003;" if t["published_booklet"] else ""
        location = t["settlement"]
        if t["neighborhood"]:
            location += f', {t["neighborhood"]}'
        rows += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd;font-weight:bold">{t["number"]}</td>
            <td style="padding:8px;border:1px solid #ddd">{t["type"]}</td>
            <td style="padding:8px;border:1px solid #ddd">{t["units"]} יח"ד</td>
            <td style="padding:8px;border:1px solid #ddd">{t["region"]}</td>
            <td style="padding:8px;border:1px solid #ddd">{location}</td>
            <td style="padding:8px;border:1px solid #ddd">{t["purpose"]}</td>
            <td style="padding:8px;border:1px solid #ddd">{t["pub_date"]}</td>
            <td style="padding:8px;border:1px solid #ddd">{t["close_date"]}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center">{booklet}</td>
        </tr>"""

    removed_note = ""
    if removed_ids:
        removed_note = f'<p style="color:#888">הוסרו {len(removed_ids)} מכרזים.</p>'

    return f"""
    <div dir="rtl" style="font-family:Arial,sans-serif;max-width:900px;margin:auto">
        <h2 style="color:#0d5aa7">מכרזי מקרקעין — {len(added)} מכרזים חדשים</h2>
        <p>סה"כ מכרזים פעילים: {total_after} (קודם: {total_before})</p>
        <table style="border-collapse:collapse;width:100%;font-size:14px">
            <thead>
                <tr style="background:#0d5aa7;color:white">
                    <th style="padding:8px;border:1px solid #ddd">מספר</th>
                    <th style="padding:8px;border:1px solid #ddd">סוג</th>
                    <th style="padding:8px;border:1px solid #ddd">יח"ד</th>
                    <th style="padding:8px;border:1px solid #ddd">מרחב</th>
                    <th style="padding:8px;border:1px solid #ddd">יישוב</th>
                    <th style="padding:8px;border:1px solid #ddd">ייעוד</th>
                    <th style="padding:8px;border:1px solid #ddd">פרסום</th>
                    <th style="padding:8px;border:1px solid #ddd">מועד אחרון</th>
                    <th style="padding:8px;border:1px solid #ddd">חוברת</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        {removed_note}
        <p style="font-size:12px;color:#888;margin-top:20px">
            <a href="https://apps.land.gov.il/MichrazimSite/#/search">צפה באתר רמ"י</a>
        </p>
    </div>
    """
