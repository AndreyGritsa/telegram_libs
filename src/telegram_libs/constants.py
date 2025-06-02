import os

required_constants = []

BOTS_AMOUNT = os.getenv("BOTS_AMOUNT")
required_constants.append(("BOTS_AMOUNT", BOTS_AMOUNT))

missing_constants = [name for name, value in required_constants if not value]
if missing_constants:
    raise ValueError(f"Required constants are not set: {', '.join(missing_constants)}")