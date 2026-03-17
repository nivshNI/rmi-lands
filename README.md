# RMI Lands — Israel Land Authority Tender Monitor

Monitors [Israel Land Authority (RMI) tenders](https://apps.land.gov.il/MichrazimSite/#/search) and notifies you via **Email**, **Telegram**, or **ntfy** when new tenders matching your filters appear.

## Quick Start

```bash
# 1. Clone & enter
cd rmi_lands

# 2. Create a virtual env
python3 -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env with your email/notification settings

# 5. Run once (first run saves a baseline)
python main.py

# 6. Run continuously (checks every 3 hours)
python main.py --loop
```

## How It Works

1. **Fetch** — Calls the RMI REST API directly (no browser needed)
2. **Filter** — Applies your configured population filter (e.g. "אנשים עם מוגבלות")
3. **Compare** — Diffs current tenders against saved snapshot
4. **Notify** — Sends you an alert with full tender details if new ones appeared

## Configuration (.env)

| Variable | Description | Default |
|---|---|---|
| `POLL_INTERVAL_SECONDS` | Seconds between checks (loop mode) | `10800` (3 hours) |
| `NOTIFY_VIA` | Comma-separated: `email`, `telegram`, `ntfy` | `email` |
| `RMI_UCHLUSIYA` | Population filter codes (see below) | `1` |

### Population Filter Codes (`RMI_UCHLUSIYA`)

| Code | Population |
|------|-----------|
| `1` | אנשים עם מוגבלות |
| `6` | חיילי מילואים |
| `4` | בני מיעוטים מומלצי כוחות הביטחון |
| `16` | בני מקום |
| `3` | חסרי דיור |

Use comma-separated values for multiple: `RMI_UCHLUSIYA=1,3`

## Notification Backends

### Email (recommended)
1. Set `NOTIFY_VIA=email`
2. For Gmail: create an [App Password](https://support.google.com/accounts/answer/185833)
3. Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO`

### Telegram
1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Get your chat ID via [@userinfobot](https://t.me/userinfobot)
3. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

### ntfy.sh (no signup)
1. Set `NOTIFY_VIA=ntfy`
2. Pick a unique `NTFY_TOPIC`
3. Subscribe on your phone: [ntfy app](https://ntfy.sh)

## Deployment

### Cron (simplest)
```bash
# Check every 3 hours
0 */3 * * * cd /path/to/rmi_lands && .venv/bin/python main.py
```

### Docker
```bash
docker build -t rmi-lands .
docker run -d --env-file .env rmi-lands
```

### GitHub Actions
Create `.github/workflows/monitor.yml` — see the repo wiki for a template.

## License

MIT
