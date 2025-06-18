from datetime import datetime
from telegram import Update
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from telegram_libs.constants import MONGO_URI, DEBUG, SUBSCRIPTION_DB_NAME
from telegram import Update


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
        self.subscription_collection = (
            self.client[SUBSCRIPTION_DB_NAME]["subscriptions"]
            if not DEBUG
            else self.client[SUBSCRIPTION_DB_NAME]["subscriptions_test"]
        )

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

    def increment_usage(self, user_id: int, field: str) -> None:
        """Increment a usage field for a user."""
        self.users_collection.update_one(
            {"user_id": user_id}, {"$inc": {field: 1}}, upsert=True
        )

    def update_user_data(self, user_id: int, updates: dict) -> None:
        """Update user data in the database."""
        self.users_collection.update_one(
            {"user_id": user_id}, {"$set": updates}, upsert=True
        )

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

    def get_user_info(self, update: Update) -> dict:
        """Get user information from the update object."""
        user = update.effective_user
        user_data = self.get_user_data(user.id)

        return {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "lang": user_data.get("language", "en"),
            **user_data,
        }

    def get_subscription(self, user_id: int) -> dict:
        """Get user's subscription data from the shared subscription database."""
        subscription = self.subscription_collection.find_one({"user_id": user_id})
        if not subscription:
            return {"user_id": user_id, "is_premium": False}
        return subscription

    def update_subscription(self, user_id: int, updates: dict) -> None:
        """Update user's subscription data in the shared subscription database."""
        self.subscription_collection.update_one(
            {"user_id": user_id}, {"$set": updates}, upsert=True
        )

    def add_subscription_payment(self, user_id: int, payment_data: dict) -> None:
        """Add a subscription payment record."""
        self.subscription_collection.update_one(
            {"user_id": user_id},
            {
                "$push": {"payments": payment_data},
                "$set": {
                    "is_premium": True,
                    "premium_expiration": payment_data["expiration_date"],
                    "last_payment": payment_data["date"],
                },
            },
            upsert=True,
        )

    def check_subscription_status(self, user_id: int) -> bool:
        """Check if user has an active subscription."""
        subscription = self.get_subscription(user_id)

        if not subscription.get("is_premium"):
            return False

        expiration = datetime.fromisoformat(subscription["premium_expiration"])
        return expiration > datetime.now()
