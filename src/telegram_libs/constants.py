import os

required_constants = []

MONGO_URI = os.getenv("MONGO_URI")
SUBSCRIPTION_DB_NAME = os.getenv("SUBSCRIPTION_DB_NAME", "subscriptions")
LOGS_DB_NAME = os.getenv("LOGS_DB_NAME", "logs")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
BOTS = {
    "https://t.me/MagMediaBot": "Remove Background",
    "https://t.me/UpscaleImage_GBot": "Upscale Image",
    "https://t.me/GanarateBackground_GBot": "Generate Background",
    "https://t.me/kudapoyti_go_bot": "Recommend Place to Visit",
    "https://t.me/TryOn_GBot": "Try On Outfit",
    "https://t.me/CloneVoice_GBot": "Clone Voice, Text to Speech AI",
    "https://t.me/SocialPoster_GBot": "Social Poster",
}

BOTS_AMOUNT = len(BOTS)

required_constants.append(("MONGO_URI", MONGO_URI))

missing_constants = [name for name, value in required_constants if not value]
if missing_constants:
    raise ValueError(f"Required constants are not set: {', '.join(missing_constants)}")