from datetime import datetime
from telegram_libs.constants import SUBSCRIPTION_DB_NAME
from telegram_libs.mongo import mongo_client

# Define the subscription database and collection
subscription_db = mongo_client[SUBSCRIPTION_DB_NAME]
subscription_collection = subscription_db["subscriptions"]


def get_subscription(user_id: int) -> dict:
    """Get user's subscription data from the shared subscription database."""
    subscription = subscription_collection.find_one({"user_id": user_id})
    if not subscription:
        return {"user_id": user_id, "is_premium": False}
    return subscription


def update_subscription(user_id: int, updates: dict) -> None:
    """Update user's subscription data in the shared subscription database."""
    subscription_collection.update_one(
        {"user_id": user_id},
        {"$set": updates},
        upsert=True
    )


def add_subscription_payment(user_id: int, payment_data: dict) -> None:
    """Add a subscription payment record."""
    subscription_collection.update_one(
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


def check_subscription_status(user_id: int) -> bool:
    """Check if user has an active subscription."""
    subscription = get_subscription(user_id)
    
    if not subscription.get("is_premium"):
        return False
        
    expiration = datetime.fromisoformat(subscription["premium_expiration"])
    return expiration > datetime.now()