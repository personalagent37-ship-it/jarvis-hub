import os
from dotenv import load_dotenv

load_dotenv()

# LLM API
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
).strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()

# Legacy Groq fallback (not used unless LLM_PROVIDER is set to groq)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192").strip()

# User
USER_NAME = "Talha"
WAKE_WORD = "jarvis"

# Voice
TTS_ENGINE = os.getenv("TTS_ENGINE", "edge")
# English and Hindi voices for Edge TTS
TTS_VOICE_EN = "en-US-ChristopherNeural"
TTS_VOICE_HI = "hi-IN-MadhurNeural"
# Default voice used when language detection fails
TTS_VOICE = TTS_VOICE_EN
TTS_RATE = "+0%"
TTS_VOLUME = "+30%"  # louder voice for clearer output
POST_SPEECH_PAUSE = float(os.getenv("POST_SPEECH_PAUSE", "0.8"))

# STT
STT_MODEL = "tiny"  # tiny model is much faster for CPUs like i3
MIC_DEVICE_NAME = "default"
STT_SILENCE_THRESHOLD = float(os.getenv('STT_SILENCE_THRESHOLD', '0.25'))
STT_MAX_DURATION = float(os.getenv("STT_MAX_DURATION", "6"))
STT_SILENCE_SECONDS   = float(os.getenv('STT_SILENCE_SECONDS',   '1.5'))
WAKE_MIN_VOLUME = float(os.getenv("WAKE_MIN_VOLUME", "0.05"))

# Portal
PORTAL_URL = os.getenv("PORTAL_URL", "").strip()

# Browser
BROWSER_ENGINE = os.getenv("BROWSER_ENGINE", "chromium").strip().lower()

# SEPIA-style local assistant runtime
USE_SEPIA_RUNTIME = os.getenv("USE_SEPIA_RUNTIME", "true").strip().lower() in {
    "1", "true", "yes", "on"
}

# Safety
CONFIRM_DANGEROUS_ACTIONS = False

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
SEPIA_COMMANDS_FILE = os.path.join(DATA_DIR, "sepia_commands.json")
ENABLE_OFFLINE_LLM = os.getenv("ENABLE_OFFLINE_LLM", "true").lower() == "true"
OFFLINE_MODEL_PATH = os.getenv("OFFLINE_MODEL_PATH", "").strip()
SAFETY_CONFIRMATION_LEVEL = os.getenv("SAFETY_CONFIRMATION_LEVEL", "high").lower()

# Home automation settings
HOME_AUTOMATION_ENABLED = os.getenv("HOME_AUTOMATION_ENABLED", "true").lower() == "true"
UI_OVERLAY_ENABLED = os.getenv("UI_OVERLAY_ENABLED", "false").lower() == "true"
HA_URL = os.getenv("HA_URL", "http://localhost:8123").strip()
HA_TOKEN = os.getenv("HA_TOKEN", "").strip()

# Car control settings (optional)
CAR_CONTROL_ENABLED = os.getenv("CAR_CONTROL_ENABLED", "true").lower() == "true"
TESLA_TOKEN = os.getenv("TESLA_TOKEN", "").strip()
