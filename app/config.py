"""
Central configuration for Mehfooz.

Every external integration (Sentinel Hub, Qwen-VL, Google Cloud, Twilio) is
optional at runtime. If credentials are missing, the corresponding module
falls back to a mock implementation so the full pipeline can run locally
for demos and tests. Check the `*_ENABLED` flags below to see what's live.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Sentinel Hub ---
SH_CLIENT_ID = os.getenv("SH_CLIENT_ID")
SH_CLIENT_SECRET = os.getenv("SH_CLIENT_SECRET")
SENTINEL_HUB_ENABLED = bool(SH_CLIENT_ID and SH_CLIENT_SECRET)

# --- Qwen-VL ---
QWEN_MODEL_NAME = os.getenv("QWEN_MODEL_NAME", "Qwen/Qwen2-VL-2B-Instruct")
QWEN_ENABLED = os.getenv("QWEN_ENABLED", "false").lower() == "true"
# Off by default: loading a real VL model needs a GPU/large download.
# Flip QWEN_ENABLED=true in .env once you're ready to run the real model.

# --- Google Cloud (Translation + TTS) ---
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_CLOUD_ENABLED = bool(GOOGLE_APPLICATION_CREDENTIALS) and os.path.exists(
    GOOGLE_APPLICATION_CREDENTIALS or ""
)

# --- Twilio ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_ENABLED = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)

# --- Celery / Redis ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mehfooz.db")

# --- Risk thresholds (tune these; current values are placeholders) ---
RISK_CRITICAL_THRESHOLD = float(os.getenv("RISK_CRITICAL_THRESHOLD", "0.65"))
RISK_WEIGHTS = {
    "area": float(os.getenv("RISK_WEIGHT_AREA", "0.5")),
    "channel": float(os.getenv("RISK_WEIGHT_CHANNEL", "0.3")),
    "melt": float(os.getenv("RISK_WEIGHT_MELT", "0.2")),
}

# --- Output/storage paths (used instead of OSS in local/demo mode) ---
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
