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
from telegram_libs.subscription import (
    get_subscription,
    update_subscription,
    add_subscription_payment,
    check_subscription_status,
    subscription_collection  # Import subscription_collection
)

@pytest.fixture(autouse=True)
def mock_subscription_collection(mock_pymongo_client):
    """Mock the subscription_collection for all tests in this module."""
    # Ensure the subscription_collection uses our patched mongo client
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_pymongo_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection

    with patch('telegram_libs.subscription.subscription_collection', new=mock_collection):
        yield mock_collection

@pytest.fixture(autouse=True)
def reset_mock(mock_subscription_collection):
    """Reset the mock before each test."""
    mock_subscription_collection.reset_mock()

class TestSubscription:
    def test_get_subscription_existing_user(self, mock_subscription_collection):
        # Setup
        user_id = 123
        mock_subscription = {
            "user_id": user_id,
            "is_premium": True,
            "premium_expiration": "2024-12-31T00:00:00"
        }
        mock_subscription_collection.find_one.return_value = mock_subscription

        # Execute
        result = get_subscription(user_id)

        # Assert
        assert result == mock_subscription
        mock_subscription_collection.find_one.assert_called_once_with({"user_id": user_id})

    def test_get_subscription_nonexistent_user(self, mock_subscription_collection):
        # Setup
        user_id = 123
        mock_subscription_collection.find_one.return_value = None

        # Execute
        result = get_subscription(user_id)

        # Assert
        assert result == {"user_id": user_id, "is_premium": False}
        mock_subscription_collection.find_one.assert_called_once_with({"user_id": user_id})

    def test_update_subscription(self, mock_subscription_collection):
        # Setup
        user_id = 123
        updates = {"is_premium": True, "premium_expiration": "2024-12-31T00:00:00"}

        # Execute
        update_subscription(user_id, updates)

        # Assert
        mock_subscription_collection.update_one.assert_called_once_with(
            {"user_id": user_id},
            {"$set": updates},
            upsert=True
        )

    def test_add_subscription_payment(self, mock_subscription_collection):
        # Setup
        user_id = 123
        payment_data = {
            "date": "2024-01-01T00:00:00",
            "expiration_date": "2024-12-31T00:00:00",
            "amount": 99.99,
            "currency": "USD"
        }

        # Execute
        add_subscription_payment(user_id, payment_data)

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

    def test_check_subscription_status_active(self, mock_subscription_collection):
        # Setup
        user_id = 123
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        mock_subscription = {
            "user_id": user_id,
            "is_premium": True,
            "premium_expiration": future_date
        }
        mock_subscription_collection.find_one.return_value = mock_subscription

        # Execute
        result = check_subscription_status(user_id)

        # Assert
        assert result is True
        mock_subscription_collection.find_one.assert_called_with({"user_id": user_id})

    def test_check_subscription_status_expired(self, mock_subscription_collection):
        # Setup
        user_id = 123
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        mock_subscription = {
            "user_id": user_id,
            "is_premium": True,
            "premium_expiration": past_date
        }
        mock_subscription_collection.find_one.return_value = mock_subscription

        # Execute
        result = check_subscription_status(user_id)

        # Assert
        assert result is False
        mock_subscription_collection.find_one.assert_called_with({"user_id": user_id})

    def test_check_subscription_status_not_premium(self, mock_subscription_collection):
        # Setup
        user_id = 123
        mock_subscription = {
            "user_id": user_id,
            "is_premium": False
        }
        mock_subscription_collection.find_one.return_value = mock_subscription

        # Execute
        result = check_subscription_status(user_id)

        # Assert
        assert result is False
        mock_subscription_collection.find_one.assert_called_with({"user_id": user_id}) 