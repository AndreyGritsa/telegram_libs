import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Set environment variables before any imports that might depend on them
os.environ['MONGO_URI'] = 'mock_mongo_uri'
os.environ['SUBSCRIPTION_DB_NAME'] = 'mock_subscription_db'
os.environ['BOTS_AMOUNT'] = '5'

@pytest.fixture(scope="module", autouse=True)
def mock_pymongo_client():
    """Patch pymongo.mongo_client.MongoClient to return a mock client."""
    with patch('pymongo.mongo_client.MongoClient') as mock_mongo_client_class:
        mock_client_instance = MagicMock()
        mock_mongo_client_class.return_value = mock_client_instance
        yield mock_client_instance

# Now import the module after MongoDB client is patched
from telegram_libs.mongo import MongoManager  # Import MongoManager

@pytest.fixture(autouse=True)
def mock_mongo_manager_and_collections(mock_pymongo_client):
    """Fixture to mock MongoManager and its client/collections."""
    mock_users_collection = MagicMock()
    mock_payments_collection = MagicMock()
    mock_subscription_collection = MagicMock()

    mock_db_subscription = MagicMock()
    mock_db_subscription.__getitem__.return_value = mock_subscription_collection
    
    mock_db_main = MagicMock()
    mock_db_main.__getitem__.side_effect = lambda key: {
        "users_test": mock_users_collection,
        "users": mock_users_collection,
        "order_test": mock_payments_collection,
        "order": mock_payments_collection,
        "subscriptions": mock_subscription_collection,
    }[key]

    mock_client = mock_pymongo_client
    mock_client.__getitem__.side_effect = lambda key: {
        "mock_subscription_db": mock_db_subscription,
        "test_db": mock_db_main,
        os.getenv("SUBSCRIPTION_DB_NAME"): mock_db_subscription
    }[key]

    with patch('telegram_libs.mongo.MongoClient', return_value=mock_client):
        # Instantiate MongoManager directly with the mock client
        mongo_manager_instance = MongoManager(mongo_database_name="test_db", client=mock_client)
        yield mongo_manager_instance, mock_subscription_collection

@pytest.fixture(autouse=True)
def reset_mock(mock_mongo_manager_and_collections):
    """Reset the mock before each test."""
    _, mock_subscription_collection = mock_mongo_manager_and_collections
    mock_subscription_collection.reset_mock()

class TestSubscription:
    def test_get_subscription_existing_user(self, mock_mongo_manager_and_collections):
        # Setup
        mongo_manager, mock_subscription_collection = mock_mongo_manager_and_collections
        user_id = 123
        mock_subscription = {
            "user_id": user_id,
            "is_premium": True,
            "premium_expiration": "2024-12-31T00:00:00"
        }
        mock_subscription_collection.find_one.return_value = mock_subscription

        # Execute
        result = mongo_manager.get_subscription(user_id)

        # Assert
        assert result == mock_subscription
        mock_subscription_collection.find_one.assert_called_once_with({"user_id": user_id})

    def test_get_subscription_nonexistent_user(self, mock_mongo_manager_and_collections):
        # Setup
        mongo_manager, mock_subscription_collection = mock_mongo_manager_and_collections
        user_id = 123
        mock_subscription_collection.find_one.return_value = None

        # Execute
        result = mongo_manager.get_subscription(user_id)

        # Assert
        assert result == {"user_id": user_id, "is_premium": False}
        mock_subscription_collection.find_one.assert_called_once_with({"user_id": user_id})

    def test_update_subscription(self, mock_mongo_manager_and_collections):
        # Setup
        mongo_manager, mock_subscription_collection = mock_mongo_manager_and_collections
        user_id = 123
        updates = {"is_premium": True, "premium_expiration": "2024-12-31T00:00:00"}

        # Execute
        mongo_manager.update_subscription(user_id, updates)

        # Assert
        mock_subscription_collection.update_one.assert_called_once_with(
            {"user_id": user_id},
            {"$set": updates},
            upsert=True
        )

    def test_add_subscription_payment(self, mock_mongo_manager_and_collections):
        # Setup
        mongo_manager, mock_subscription_collection = mock_mongo_manager_and_collections
        user_id = 123
        payment_data = {
            "date": "2024-01-01T00:00:00",
            "expiration_date": "2024-12-31T00:00:00",
            "amount": 99.99,
            "currency": "USD"
        }

        # Execute
        mongo_manager.add_subscription_payment(user_id, payment_data)

        # Assert
        mock_subscription_collection.update_one.assert_called_once_with(
            {"user_id": user_id},
            {
                "$push": {"payments": payment_data},
                "$set": {
                    "is_premium": True,
                    "premium_expiration": payment_data["expiration_date"],
                    "last_payment": payment_data["date"]
                }
            },
            upsert=True
        )

    def test_check_subscription_status_active(self, mock_mongo_manager_and_collections):
        # Setup
        mongo_manager, mock_subscription_collection = mock_mongo_manager_and_collections
        user_id = 123
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        mock_subscription = {
            "user_id": user_id,
            "is_premium": True,
            "premium_expiration": future_date
        }
        mock_subscription_collection.find_one.return_value = mock_subscription

        # Execute
        result = mongo_manager.check_subscription_status(user_id)

        # Assert
        assert result is True
        mock_subscription_collection.find_one.assert_called_with({"user_id": user_id})

    def test_check_subscription_status_expired(self, mock_mongo_manager_and_collections):
        # Setup
        mongo_manager, mock_subscription_collection = mock_mongo_manager_and_collections
        user_id = 123
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        mock_subscription = {
            "user_id": user_id,
            "is_premium": True,
            "premium_expiration": past_date
        }
        mock_subscription_collection.find_one.return_value = mock_subscription

        # Execute
        result = mongo_manager.check_subscription_status(user_id)

        # Assert
        assert result is False
        mock_subscription_collection.find_one.assert_called_with({"user_id": user_id})

    def test_check_subscription_status_not_premium(self, mock_mongo_manager_and_collections):
        # Setup
        mongo_manager, mock_subscription_collection = mock_mongo_manager_and_collections
        user_id = 123
        mock_subscription = {
            "user_id": user_id,
            "is_premium": False
        }
        mock_subscription_collection.find_one.return_value = mock_subscription

        # Execute
        result = mongo_manager.check_subscription_status(user_id)

        # Assert
        assert result is False
        mock_subscription_collection.find_one.assert_called_with({"user_id": user_id}) 