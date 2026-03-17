import json
import os

from dotenv import load_dotenv

load_dotenv()


def _parse_int_list(val: str) -> list[int]:
    if not val:
        return []
    return [int(x.strip()) for x in val.split(",") if x.strip()]


class Config:
    POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL_SECONDS", "10800"))  # 3 hours

    NOTIFY_VIA: str = os.getenv("NOTIFY_VIA", "email")

    # ntfy
    NTFY_TOPIC: str = os.getenv("NTFY_TOPIC", "rmi-lands-alerts")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Email (SMTP)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_TO: str = os.getenv("EMAIL_TO", "")

    # RMI search filters
    # Population priority codes: 1=אנשים עם מוגבלות, 6=חיילי מילואים,
    # 4=בני מיעוטים, 16=בני מקום, 3=חסרי דיור
    RMI_UCHLUSIYA: list[int] = _parse_int_list(os.getenv("RMI_UCHLUSIYA", "1"))

    # Optional: LLM summarization
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    USE_LLM_SUMMARY: bool = os.getenv("USE_LLM_SUMMARY", "false").lower() == "true"
