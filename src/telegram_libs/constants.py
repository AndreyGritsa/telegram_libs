import os

required_constants = []

MONGO_URI = os.getenv("MONGO_URI")
SUBSCRIPTION_DB_NAME = os.getenv("SUBSCRIPTION_DB_NAME")
LOGS_DB_NAME = os.getenv("LOGS_DB_NAME", "logs")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
BOTS = {
    "https://t.me/MagMediaBot": "Remove Background",
    "https://t.me/UpscaleImageGBot": "Upscale Image",
    "https://t.me/GenerateBackgroundGBot": "Generate Background",
    "https://t.me/kudapoyti_go_bot": "Recommend Place to Visit",
    "https://t.me/TryOnOutfitGBot": "Try On Outfit",
    "https://t.me/CloneVoiceAIGBot": "Clone Voice, Text to Speech AI",
}

BOTS_AMOUNT = len(BOTS)

required_constants.append(("MONGO_URI", MONGO_URI))
required_constants.append(("SUBSCRIPTION_DB_NAME", SUBSCRIPTION_DB_NAME))

missing_constants = [name for name, value in required_constants if not value]
if missing_constants:
    raise ValueError(f"Required constants are not set: {', '.join(missing_constants)}")