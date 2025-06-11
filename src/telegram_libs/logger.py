from datetime import datetime
from telegram_libs.mongo import MongoManager
from telegram_libs.constants import DEBUG, LOGS_DB_NAME


class BotLogger:
    def __init__(self):
        self.mongo_manager = MongoManager(mongo_database_name=LOGS_DB_NAME)
        self.logs_collection = (
            self.mongo_manager.client[LOGS_DB_NAME]["logs_test"]
            if DEBUG
            else self.mongo_manager.client[LOGS_DB_NAME]["logs"]
        )

    def log_action(
        self, user_id: int, action_type: str, bot_name: str, details: dict = None
    ) -> None:
        """Log a user action to the database."""
        log_entry = {
            "user_id": user_id,
            "action_type": action_type,
            "bot_name": bot_name,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
        self.logs_collection.insert_one(log_entry) 