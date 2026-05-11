"""Application configuration settings."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/whatsapp.db"

# WhatsApp Web
WHATSAPP_SESSION_FILE = DATA_DIR / "whatsapp_session.json"
QR_CODE_FILE = DATA_DIR / "qr_code.png"

# Chrome options for headless mode
CHROME_OPTIONS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1200,800",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
]

# Timezone
DEFAULT_TIMEZONE = "UTC"

# Scheduler
SCHEDULER_CHECK_INTERVAL = 60  # seconds

# API settings
API_TITLE = "WhatsApp Automation API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "API for WhatsApp messaging automation"

# CORS
CORS_ORIGINS = ["*"]

# Message statuses
MESSAGE_STATUS_PENDING = "pending"
MESSAGE_STATUS_SENT = "sent"
MESSAGE_STATUS_FAILED = "failed"
MESSAGE_STATUS_SCHEDULED = "scheduled"