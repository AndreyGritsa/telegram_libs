from datetime import datetime, timedelta
from logging import getLogger
from telegram import Update
from telegram.ext import ContextTypes
from telegram_libs.translation import t
from telegram_libs.subscription import add_subscription_payment
from telegram_libs.utils import get_user_info
from telegram_libs.mongo import MongoManager
from telegram_libs.logger import BotLogger

logger = getLogger(__name__)


async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the pre-checkout query"""
    query = update.pre_checkout_query
    user_id = query.from_user.id

    # Always accept the pre-checkout query in this basic implementation
    # You could add additional validation here if needed (e.g., check user status, inventory, etc.)

    try:
        await query.answer(ok=True)
        logger.info(f"Pre-checkout approved for user {user_id}")
    except Exception as e:
        logger.error(f"Error answering pre-checkout query: {e}")
        # Try to answer with error if something went wrong
        try:
            await query.answer(
                ok=False,
                error_message="An error occurred while processing your payment",
            )
        except Exception as e2:
            logger.error(f"Error sending pre-checkout error: {e2}")


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, mongo_manager: MongoManager, bot_logger: BotLogger) -> None:
    """Handle successful payments"""
    user_info = get_user_info(update, mongo_manager)
    user_id = user_info["user_id"]
    lang = user_info["lang"]
    payment_info = update.message.successful_payment
    bot_name = context.bot.name
    bot_logger.log_action(user_id, "successful_payment", bot_name, {"payload": payment_info.invoice_payload, "amount": payment_info.total_amount, "currency": payment_info.currency})
    logger.info(f"Payment info received: {payment_info}")

    # Determine which plan was purchased
    plans = {"1month_sub": 30, "3months_sub": 90, "1year_sub": 365}

    duration_days = plans.get(payment_info.invoice_payload, 0)
    if duration_days == 0:
        logger.warning(f"Invalid subscription plan: {payment_info.invoice_payload}")
        await update.message.reply_text(
            t("subscription.payment_issue", lang, common=True)
        )
        return

    # Add order to bot-specific database
    mongo_manager.add_order(
        user_id,
        {
            "order_id": payment_info.provider_payment_charge_id,
            "amount": payment_info.total_amount,
            "currency": payment_info.currency,
            "status": "completed",
            "date": datetime.now().isoformat(),
        },
    )

    # Calculate expiration date
    expiration_date = datetime.now() + timedelta(days=duration_days)
    current_time = datetime.now()

    # Add subscription payment to shared subscription database
    add_subscription_payment(
        user_id,
        {
            "order_id": payment_info.provider_payment_charge_id,
            "amount": payment_info.total_amount,
            "currency": payment_info.currency,
            "status": "completed",
            "date": current_time.isoformat(),
            "expiration_date": expiration_date.isoformat(),
            "plan": payment_info.invoice_payload,
            "duration_days": duration_days
        }
    )

    logger.info(
        f"User {user_id} subscribed successfully. Premium expires on {expiration_date.isoformat()}."
    )

    await update.message.reply_text(
        t("subscription.success", lang, common=True).format(
            date=expiration_date.strftime("%Y-%m-%d")
        )
    )
