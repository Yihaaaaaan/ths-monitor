# ths-monitor

Polls public TrustedHousesitters search pages and sends a Telegram alert when a
new sit appears that still has application slots open. Discovery only — no
login, no cookies, no automated applying.

Runs on GitHub Actions every ~10 minutes (`.github/workflows/monitor.yml`).
State (seen assignment ids) is committed back to `state.json`.

Secrets required: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
