import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# Set required environment variables for the imports that depend on them
os.environ["BOTS_AMOUNT"] = "5"
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["SUBSCRIPTION_DB_NAME"] = "subscription_db"

from telegram import Update
from telegram.ext import ContextTypes
from telegram_libs.payment import precheckout_handler, successful_payment
from telegram_libs.mongo import MongoManager
from telegram_libs.translation import t


@pytest.fixture
def mock_update_precheckout():
    update = MagicMock(spec=Update)
    update.pre_checkout_query = MagicMock()
    update.pre_checkout_query.from_user.id = 12345
    update.pre_checkout_query.answer = AsyncMock()
    return update


@pytest.fixture
def mock_update_successful_payment():
    update = MagicMock(spec=Update)
    update.message = MagicMock()
    update.message.successful_payment = MagicMock()
    update.message.successful_payment.provider_payment_charge_id = "test_charge_id"
    update.message.successful_payment.total_amount = 1000
    update.message.successful_payment.currency = "XTR"
    update.message.successful_payment.invoice_payload = "1month_sub"
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


@pytest.fixture
def mock_mongo_manager():
    manager = MagicMock(spec=MongoManager)
    manager.add_order = MagicMock()
    return manager


@pytest.mark.asyncio
async def test_precheckout_handler_success(mock_update_precheckout, mock_context):
    await precheckout_handler(mock_update_precheckout, mock_context)
    mock_update_precheckout.pre_checkout_query.answer.assert_called_once_with(ok=True)


@pytest.mark.asyncio
async def test_precheckout_handler_error(mock_update_precheckout, mock_context):
    mock_update_precheckout.pre_checkout_query.answer.side_effect = Exception("Test Error")
    await precheckout_handler(mock_update_precheckout, mock_context)
    mock_update_precheckout.pre_checkout_query.answer.assert_called_with(ok=False, error_message="An error occurred while processing your payment")


@pytest.mark.asyncio
@patch("telegram_libs.payment.get_user_info")
@patch("telegram_libs.payment.add_subscription_payment")
@patch("telegram_libs.payment.datetime")
async def test_successful_payment_valid_plan(
    mock_datetime,
    mock_add_subscription_payment,
    mock_get_user_info,
    mock_update_successful_payment,
    mock_context,
    mock_mongo_manager,
):
    # Mock get_user_info
    mock_get_user_info.return_value = {"user_id": 123, "lang": "en"}

    # Mock datetime.now() for consistent testing
    fixed_now = datetime(2024, 1, 1, 10, 0, 0)
    mock_datetime.now.return_value = fixed_now
    mock_datetime.isoformat.side_effect = fixed_now.isoformat
    mock_datetime.strftime.side_effect = lambda x: fixed_now.strftime(x)
    mock_datetime.timedelta = timedelta

    await successful_payment(
        mock_update_successful_payment, mock_context, mock_mongo_manager
    )

    # Assertions
    mock_get_user_info.assert_called_once_with(
        mock_update_successful_payment, mock_mongo_manager
    )
    mock_mongo_manager.add_order.assert_called_once_with(
        123,
        {
            "order_id": "test_charge_id",
            "amount": 1000,
            "currency": "XTR",
            "status": "completed",
            "date": fixed_now.isoformat(),
        },
    )

    expected_expiration_date = fixed_now + timedelta(days=30)
    mock_add_subscription_payment.assert_called_once_with(
        123,
        {
            "order_id": "test_charge_id",
            "amount": 1000,
            "currency": "XTR",
            "status": "completed",
            "date": fixed_now.isoformat(),
            "expiration_date": expected_expiration_date.isoformat(),
            "plan": "1month_sub",
            "duration_days": 30,
        },
    )

    mock_update_successful_payment.message.reply_text.assert_called_once_with(
        t("subscription.success", "en", common=True).format(
            date=expected_expiration_date.strftime("%Y-%m-%d")
        )
    )


@pytest.mark.asyncio
@patch("telegram_libs.payment.get_user_info")
@patch("telegram_libs.payment.t")
async def test_successful_payment_invalid_plan(
    mock_t,
    mock_get_user_info,
    mock_update_successful_payment,
    mock_context,
    mock_mongo_manager,
):
    # Mock get_user_info
    mock_get_user_info.return_value = {"user_id": 123, "lang": "en"}

    # Set an invalid invoice_payload
    mock_update_successful_payment.message.successful_payment.invoice_payload = (
        "invalid_plan"
    )

    await successful_payment(
        mock_update_successful_payment, mock_context, mock_mongo_manager
    )

    # Assertions
    mock_get_user_info.assert_called_once_with(
        mock_update_successful_payment, mock_mongo_manager
    )
    mock_update_successful_payment.message.reply_text.assert_called_once_with(
        mock_t("subscription.payment_issue", "en", common=True)
    )
    mock_mongo_manager.add_order.assert_not_called()
    # Ensure add_subscription_payment was not called for invalid plan
    with patch("telegram_libs.payment.add_subscription_payment") as mock_add_subscription_payment:
        mock_add_subscription_payment.assert_not_called() 