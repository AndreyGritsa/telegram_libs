import os 

os.environ["BOTS_AMOUNT"] = "5"
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["SUBSCRIPTION_DB_NAME"] = "subscription_db"

import pytest
from unittest.mock import MagicMock
from telegram_libs.mongo import MongoManager
from telegram_libs.constants import DEBUG

@pytest.fixture
def mock_mongo_collections():
    mock_users_collection = MagicMock()
    mock_payments_collection = MagicMock()
    mock_subscription_collection = MagicMock()
    mock_db = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: {
        "users_test": mock_users_collection,
        "users": mock_users_collection,
        "order_test": mock_payments_collection,
        "order": mock_payments_collection,
        "subscriptions": mock_subscription_collection,
    }[key]
    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    return mock_client, mock_users_collection, mock_payments_collection, mock_subscription_collection

@pytest.fixture
def mongo_manager(mock_mongo_collections):
    mock_client, _, _, mock_subscription_collection = mock_mongo_collections
    return MongoManager(mongo_database_name="test_db", client=mock_client, user_schema={"location": None, "recommended": []})


class TestMongoManager:
    def test_init(self, mongo_manager, mock_mongo_collections):
        mock_client, mock_users_collection, mock_payments_collection, mock_subscription_collection = mock_mongo_collections
        
        assert mongo_manager.client == mock_client
        assert mongo_manager.db == mock_client.__getitem__.return_value
        
        if DEBUG:
            assert mongo_manager.users_collection == mock_users_collection
            assert mongo_manager.payments_collection == mock_payments_collection
            assert mongo_manager.subscription_collection == mock_subscription_collection
        else:
            assert mongo_manager.users_collection == mock_users_collection
            assert mongo_manager.payments_collection == mock_payments_collection
            assert mongo_manager.subscription_collection == mock_subscription_collection
            
        assert mongo_manager.user_schema == {"user_id": None, "location": None, "recommended": []}

    def test_create_user(self, mongo_manager):
        user_id = 123
        
        # Mock the insert_one method
        mongo_manager.users_collection.insert_one = MagicMock()
        
        result = mongo_manager.create_user(user_id)
        
        # Assert that insert_one was called with the correct data
        expected_user_data = {"user_id": user_id, "location": None, "recommended": []}
        mongo_manager.users_collection.insert_one.assert_called_once_with(expected_user_data)
        
        # Assert the return value
        assert result == expected_user_data

    def test_get_user_data_existing_user(self, mongo_manager):
        user_id = 123
        existing_user_data = {"user_id": user_id, "location": "New York"}
        mongo_manager.users_collection.find_one.return_value = existing_user_data
        
        result = mongo_manager.get_user_data(user_id)
        
        mongo_manager.users_collection.find_one.assert_called_once_with({"user_id": user_id})
        assert result == existing_user_data

    def test_get_user_data_nonexistent_user(self, mongo_manager):
        user_id = 123
        mongo_manager.users_collection.find_one.return_value = None
        
        # Mock create_user to control its behavior and check if it's called
        mongo_manager.create_user = MagicMock(return_value={
            "user_id": user_id,
            "location": None,
            "recommended": []
        })
        
        result = mongo_manager.get_user_data(user_id)
        
        mongo_manager.users_collection.find_one.assert_called_once_with({"user_id": user_id})
        mongo_manager.create_user.assert_called_once_with(user_id)
        assert result == {"user_id": user_id, "location": None, "recommended": []}

    def test_update_user_data_existing_user(self, mongo_manager, monkeypatch):
        user_id = 123
        updates = {"location": "London"}
        
        # Mock update_one to simulate a matched document
        mock_update_result = MagicMock()
        mock_update_result.matched_count = 1
        mongo_manager.users_collection.update_one.return_value = mock_update_result
        
        # Mock create_user to ensure it's not called
        monkeypatch.setattr(mongo_manager, 'create_user', MagicMock())
        
        mongo_manager.update_user_data(user_id, updates)
        
        mongo_manager.users_collection.update_one.assert_called_once_with(
            {"user_id": user_id}, {"$set": updates}
        )
        mongo_manager.create_user.assert_not_called()

    def test_update_user_data_nonexistent_user(self, mongo_manager, monkeypatch):
        user_id = 123
        updates = {"location": "Paris"}
        
        # Mock update_one to simulate no matched document initially
        mock_update_result = MagicMock()
        mock_update_result.matched_count = 0
        mongo_manager.users_collection.update_one.return_value = mock_update_result
        
        # Mock create_user
        mock_create_user = MagicMock()
        monkeypatch.setattr(mongo_manager, 'create_user', mock_create_user)
        
        mongo_manager.update_user_data(user_id, updates)
        
        # Assert create_user was called once
        mock_create_user.assert_called_once_with(user_id)
        
        # Assert update_one was called twice: once for the initial update, once after creation
        assert mongo_manager.users_collection.update_one.call_count == 2
        mongo_manager.users_collection.update_one.assert_any_call(
            {"user_id": user_id}, {"$set": updates}
        )

    def test_add_order(self, mongo_manager):
        user_id = 123
        order = {"order_id": 1, "amount": 100}
        
        mongo_manager.payments_collection.insert_one = MagicMock()
        
        mongo_manager.add_order(user_id, order)
        
        mongo_manager.payments_collection.insert_one.assert_called_once_with(
            {"user_id": user_id, "order_id": 1, "amount": 100}
        )

    def test_get_orders(self, mongo_manager):
        user_id = 123
        mock_orders = [
            {"user_id": user_id, "order_id": 1},
            {"user_id": user_id, "order_id": 2}
        ]
        
        # Mock find to return an iterable (like a cursor)
        mongo_manager.payments_collection.find.return_value = mock_orders
        
        result = mongo_manager.get_orders(user_id)
        
        mongo_manager.payments_collection.find.assert_called_once_with({"user_id": user_id})
        assert result == mock_orders

    def test_update_order(self, mongo_manager):
        user_id = 123
        order_id = 1
        updates = {"status": "completed"}
        
        mongo_manager.payments_collection.update_one = MagicMock()
        
        mongo_manager.update_order(user_id, order_id, updates)
        
        mongo_manager.payments_collection.update_one.assert_called_once_with(
            {"user_id": user_id, "order_id": order_id}, {"$set": updates}
        ) 