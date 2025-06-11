import pytest
from unittest.mock import MagicMock, patch

# Set environment variables for constants used in BotLogger
import os
os.environ["LOGS_DB_NAME"] = "test_logs_db"
os.environ["DEBUG"] = "True"
os.environ["BOTS_AMOUNT"] = "5"
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["SUBSCRIPTION_DB_NAME"] = "subscription_db"

from telegram_libs.logger import BotLogger
from telegram_libs.constants import LOGS_DB_NAME, DEBUG


@pytest.fixture
def mock_mongo_manager():
    """Fixture to mock MongoManager and its client/collections."""
    mock_collection = MagicMock()
    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db

    with patch("telegram_libs.logger.MongoManager") as MockMongoManager:
        mock_mongo_manager_instance = MockMongoManager.return_value
        mock_mongo_manager_instance.client = mock_client
        yield MockMongoManager, mock_collection


class TestBotLogger:
    def test_init(self, mock_mongo_manager):
        MockMongoManager_class, mock_collection = mock_mongo_manager
        
        logger = BotLogger()

        MockMongoManager_class.assert_called_once_with(mongo_database_name=LOGS_DB_NAME)
        
        # Assert that logs_collection is correctly assigned based on DEBUG
        expected_collection_name = "logs_test" if DEBUG else "logs"
        MockMongoManager_class.return_value.client.__getitem__.assert_any_call(LOGS_DB_NAME)
        MockMongoManager_class.return_value.client.__getitem__.return_value.__getitem__.assert_called_once_with(expected_collection_name)
        assert logger.logs_collection == mock_collection

    @patch("telegram_libs.logger.datetime")
    def test_log_action(self, mock_datetime, mock_mongo_manager):
        MockMongoManager_class, mock_collection = mock_mongo_manager
        
        # Setup for datetime mocking
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2024-01-01T12:00:00"
        mock_datetime.now.return_value = mock_now

        logger = BotLogger()

        user_id = 123
        action_type = "test_action"
        bot_name = "TestBot"
        details = {"key": "value"}

        logger.log_action(user_id, action_type, bot_name, details)

        expected_log_entry = {
            "user_id": user_id,
            "action_type": action_type,
            "bot_name": bot_name,
            "timestamp": "2024-01-01T12:00:00",
            "details": details,
        }
        mock_collection.insert_one.assert_called_once_with(expected_log_entry)

    @patch("telegram_libs.logger.datetime")
    def test_log_action_no_details(self, mock_datetime, mock_mongo_manager):
        MockMongoManager_class, mock_collection = mock_mongo_manager
        
        # Setup for datetime mocking
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2024-01-01T12:00:00"
        mock_datetime.now.return_value = mock_now

        logger = BotLogger()

        user_id = 456
        action_type = "another_action"
        bot_name = "AnotherBot"

        logger.log_action(user_id, action_type, bot_name)

        expected_log_entry = {
            "user_id": user_id,
            "action_type": action_type,
            "bot_name": bot_name,
            "timestamp": "2024-01-01T12:00:00",
            "details": {},
        }
        mock_collection.insert_one.assert_called_once_with(expected_log_entry) 