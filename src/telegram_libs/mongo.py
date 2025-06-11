from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from telegram_libs.constants import MONGO_URI, DEBUG


class MongoManager:
    _mongo_client = None

    @property
    def mongo_client(self):
        if self._mongo_client is None:
            self._mongo_client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
        return self._mongo_client

    def __init__(self, mongo_database_name: str, **kwargs):
        self.client = kwargs.get("client") or self.mongo_client
        self.db = self.client[mongo_database_name]
        self.users_collection = self.db["users_test"] if DEBUG else self.db["users"]
        self.payments_collection = self.db["order_test"] if DEBUG else self.db["order"]
        self.user_schema = {"user_id": None, **(kwargs.get("user_schema") or {})}

    def create_user(self, user_id: int) -> None:
        """Create a new user in the database."""
        user_data = self.user_schema.copy()
        user_data["user_id"] = user_id
        self.users_collection.insert_one(user_data)
        return user_data

    def get_user_data(self, user_id: int) -> dict:
        """Retrieve user data from the database."""
        user_data = self.users_collection.find_one({"user_id": user_id})
        if not user_data:
            # Initialize user data if not found
            return self.create_user(user_id)
        return user_data

    def update_user_data(self, user_id: int, updates: dict) -> None:
        """Update user data in the database."""
        result = self.users_collection.update_one({"user_id": user_id}, {"$set": updates})
        if result.matched_count == 0:
            # If no document was matched, create a new user
            self.create_user(user_id)
            self.users_collection.update_one({"user_id": user_id}, {"$set": updates})

    def add_order(self, user_id: int, order: dict) -> None:
        """Add an order to the user's data."""
        self.payments_collection.insert_one({"user_id": user_id, **order})


    def get_orders(self, user_id: int) -> list:
        """Get all orders for a user."""
        orders = self.payments_collection.find({"user_id": user_id})
        return list(orders)


    def update_order(self, user_id: int, order_id: int, updates: dict) -> None:
        """Update an order for a user."""
        self.payments_collection.update_one(
            {"user_id": user_id, "order_id": order_id}, {"$set": updates}
        )