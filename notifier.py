"""
Notification backends — ntfy, Telegram, Email.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import httpx

from config import Config

logger = logging.getLogger(__name__)


def notify(title: str, message: str, html_message: Optional[str] = None) -> None:
    backends = [b.strip().lower() for b in Config.NOTIFY_VIA.split(",")]
    for backend in backends:
        try:
            if backend == "ntfy":
                _send_ntfy(title, message)
            elif backend == "telegram":
                _send_telegram(title, message)
            elif backend == "email":
                _send_email(title, message, html_message)
            else:
                logger.warning("Unknown notification backend: %s", backend)
        except Exception:
            logger.exception("Failed to send via %s", backend)


def _send_ntfy(title: str, message: str) -> None:
    url = f"https://ntfy.sh/{Config.NTFY_TOPIC}"
    httpx.post(url, content=message.encode(), headers={"Title": title}, timeout=10)
    logger.info("ntfy notification sent to topic '%s'", Config.NTFY_TOPIC)


def _send_telegram(title: str, message: str) -> None:
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"*{title}*\n\n{message}", "parse_mode": "Markdown"}
    resp = httpx.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    logger.info("Telegram notification sent to chat %s", chat_id)


def _send_email(title: str, plain: str, html: Optional[str] = None) -> None:
    if not Config.SMTP_USER or not Config.EMAIL_TO:
        raise ValueError("SMTP_USER and EMAIL_TO must be set")

    if html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
    else:
        msg = MIMEText(plain, "plain", "utf-8")

    msg["Subject"] = title
    msg["From"] = Config.SMTP_USER
    msg["To"] = Config.EMAIL_TO

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.send_message(msg)
    logger.info("Email sent to %s", Config.EMAIL_TO)
