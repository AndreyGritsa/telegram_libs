import os

required_constants = []

BOTS_AMOUNT = os.getenv("BOTS_AMOUNT")
MONGO_URI = os.getenv("MONGO_URI")
SUBSCRIPTION_DB_NAME = os.getenv("SUBSCRIPTION_DB_NAME")

required_constants.append(("BOTS_AMOUNT", BOTS_AMOUNT))
required_constants.append(("MONGO_URI", MONGO_URI))
required_constants.append(("SUBSCRIPTION_DB_NAME", SUBSCRIPTION_DB_NAME))

missing_constants = [name for name, value in required_constants if not value]
if missing_constants:
    raise ValueError(f"Required constants are not set: {', '.join(missing_constants)}")