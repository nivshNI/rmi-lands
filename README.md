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
5. **Map** — Regenerates `docs/index.html` from the same snapshot

## The Map

Every run rebuilds an interactive map of all active tenders at `docs/index.html`.
Serve it with GitHub Pages (**Settings → Pages → Deploy from branch → `/docs`**),
or just open the file locally — Leaflet is vendored into `docs/vendor/`, so the
only thing it fetches at runtime is the OpenStreetMap basemap.

- **One dot per tender**, colored by tender type (`סוג המכרז`)
- **Filters** for tender type, purpose (`ייעוד מכרז`), region, and free-text search
- **Hover** any dot for full details, with the opening date shown up front
- **Click** a dot to star it or open it on the RMI site
- **Table view** lists the same filtered set, sortable by eye and copy-pasteable

### Marker precision

Tenders carry a settlement name, not coordinates, so the map geocodes them
against a bundled dataset (`geo/settlements.json`, 1365 localities). Each marker
declares how it was placed:

| Tier | Meaning | Marker |
|---|---|---|
| `exact` | Matched a settlement point | Solid |
| `approx` | Curated coordinate (regional councils, spelling variants) | Faded, dashed |
| `region` | No settlement match — placed at the region centre | Faded, dashed |

On the current snapshot that resolves to 398 exact, 74 approx, and 7 region-only
(names like `לא ידוע` that identify no real place).

## Watchlist (⭐)

Star tenders to get a **separate Telegram/email alert whenever their details
change** — opening date, closing date, booklet publication, unit count, purpose,
and more — not just when new tenders appear.

`watchlist.json` is what the monitor reads:

```json
{ "ids": ["20260167", "20210409"] }
```

The map page is static and cannot write to the repo, so starring works like this:

1. Star tenders on the map (kept in your browser)
2. A bar appears — hit **העתק JSON**, then **ערוך ב־GitHub**
3. Paste, commit, done — the next run starts watching them

To skip the map entirely, just edit `watchlist.json` by hand.

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
