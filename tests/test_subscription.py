import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Set environment variables before any imports that might depend on them
os.environ['MONGO_URI'] = 'mock_mongo_uri'
os.environ['SUBSCRIPTION_DB_NAME'] = 'mock_subscription_db'
os.environ['BOTS_AMOUNT'] = '5'

# Create mock collection
mock_collection = MagicMock()

# Patch MongoDB client before importing the module
with patch('telegram_libs.mongo.mongo_client') as mock_mongo_client:
    mock_mongo_client.__getitem__.return_value.__getitem__.return_value = mock_collection
    
    # Now import the module after MongoDB client is patched
    from telegram_libs.subscription import (
        get_subscription,
        update_subscription,
        add_subscription_payment,
        check_subscription_status
    )

@pytest.fixture(autouse=True)
def reset_mock():
    """Reset the mock before each test."""
    mock_collection.reset_mock()

class TestSubscription:
    def test_get_subscription_existing_user(self):
        # Setup
        user_id = 123
        mock_subscription = {
            "user_id": user_id,
            "is_premium": True,
            "premium_expiration": "2024-12-31T00:00:00"
        }
        mock_collection.find_one.return_value = mock_subscription

        # Execute
        result = get_subscription(user_id)

        # Assert
        assert result == mock_subscription
        mock_collection.find_one.assert_called_once_with({"user_id": user_id})

    def test_get_subscription_nonexistent_user(self):
        # Setup
        user_id = 123
        mock_collection.find_one.return_value = None

        # Execute
        result = get_subscription(user_id)

        # Assert
        assert result == {"user_id": user_id, "is_premium": False}
        mock_collection.find_one.assert_called_once_with({"user_id": user_id})

    def test_update_subscription(self):
        # Setup
        user_id = 123
        updates = {"is_premium": True, "premium_expiration": "2024-12-31T00:00:00"}

        # Execute
        update_subscription(user_id, updates)

        # Assert
        mock_collection.update_one.assert_called_once_with(
            {"user_id": user_id},
            {"$set": updates},
            upsert=True
        )

    def test_add_subscription_payment(self):
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
        mock_collection.update_one.assert_called_once_with(
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

    def test_check_subscription_status_active(self):
        # Setup
        user_id = 123
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        mock_subscription = {
            "user_id": user_id,
            "is_premium": True,
            "premium_expiration": future_date
        }
        mock_collection.find_one.return_value = mock_subscription

        # Execute
        result = check_subscription_status(user_id)

        # Assert
        assert result is True
        mock_collection.find_one.assert_called_with({"user_id": user_id})

    def test_check_subscription_status_expired(self):
        # Setup
        user_id = 123
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        mock_subscription = {
            "user_id": user_id,
            "is_premium": True,
            "premium_expiration": past_date
        }
        mock_collection.find_one.return_value = mock_subscription

        # Execute
        result = check_subscription_status(user_id)

        # Assert
        assert result is False
        mock_collection.find_one.assert_called_with({"user_id": user_id})

    def test_check_subscription_status_not_premium(self):
        # Setup
        user_id = 123
        mock_subscription = {
            "user_id": user_id,
            "is_premium": False
        }
        mock_collection.find_one.return_value = mock_subscription

        # Execute
        result = check_subscription_status(user_id)

        # Assert
        assert result is False
        mock_collection.find_one.assert_called_with({"user_id": user_id}) 