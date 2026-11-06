import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

# Official OwO Bot Discord ID
OWO_BOT_ID = 408785106942164992

# Betting Settings
BASE_BET = 10000
MAX_BET = 250000

# Randomized Delay Range (in seconds)
MIN_DELAY = 16.5
MAX_DELAY = 24.5

# Command Variations (Amount inke baad lag kar jayega)
COMMAND_PREFIXES = [
    "owo Coinflip",
    "owo coinflip",
    "ocf",
    "owo cf",
    "o coinflip",
    "o cf",
    "Owo cf",
    "OWO coinflip"
]

# Captcha / Verification Triggers
CAPTCHA_KEYWORDS = [
    "captcha",
    "verify that you are human",
    "are you a real human",
    "please complete",
    "please use the link",
    "⚠️",
    "🔒",
    "banned"
]