from datetime import datetime, timedelta
from telegram import Update, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram_libs.constants import BOTS_AMOUNT, DEBUG
from telegram_libs.mongo import MongoManager
from telegram_libs.translation import t
from telegram_libs.logger import BotLogger


async def get_subscription_keyboard(update: Update, lang: str) -> InlineKeyboardMarkup:
    """Get subscription keyboard

    Args:
        update (Update): Update object
        lang (str): Language code

    Returns:
        InlineKeyboardMarkup: Inline keyboard markup
    """
    await update.message.reply_text(
        t("subscription.info", lang, common=True).format(int(BOTS_AMOUNT) - 1)
    )
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                t("subscription.plans.1month", lang, common=True), callback_data="sub_1month"
            ),
            InlineKeyboardButton(
                t("subscription.plans.3months", lang, common=True), callback_data="sub_3months"
            ),
        ],
        [
            InlineKeyboardButton(
                t("subscription.plans.1year", lang, common=True), callback_data="sub_1year"
            ),
        ],
    ])


async def subscription_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, bot_logger: BotLogger
) -> None:
    """Handle subscription button clicks"""
    query = update.callback_query
    user_id = query.from_user.id
    bot_name = context.bot.name
    bot_logger.log_action(user_id, "subscription_button_click", bot_name, {"plan": query.data})
    await query.answer()
    plan = query.data

    # Define subscription plans
    plans = {
        "sub_1month": {
            "title": "1 Month Subscription",
            "description": "Premium access for 1 month",
            "payload": "1month_sub",
            "price": 400 if not DEBUG else 1,
            "duration": 30,
        },
        "sub_3months": {
            "title": "3 Months Subscription",
            "description": "Premium access for 3 months",
            "payload": "3months_sub",
            "price": 1100 if not DEBUG else 1,
            "duration": 90,
        },
        "sub_1year": {
            "title": "1 Year Subscription",
            "description": "Premium access for 1 year",
            "payload": "1year_sub",
            "price": 3600 if not DEBUG else 1,
            "duration": 365,
        },
    }

    selected_plan = plans.get(plan)
    if not selected_plan:
        await query.message.reply_text("Invalid subscription option")
        return

    # Create invoice for Telegram Stars
    prices = [LabeledPrice(selected_plan["title"], selected_plan["price"])]

    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=selected_plan["title"],
        description=selected_plan["description"],
        payload=selected_plan["payload"],
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="subscription",
    )


async def subscribe_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, mongo_manager: MongoManager, bot_logger: BotLogger
) -> None:
    """Show subscription options"""
    user_info = mongo_manager.get_user_info(update)
    user_id = user_info["user_id"]
    lang = user_info["lang"]
    bot_name = context.bot.name
    bot_logger.log_action(user_id, "subscribe_command", bot_name)

    reply_markup = await get_subscription_keyboard(update, lang)

    await update.message.reply_text(
        t("subscription.choose_plan", lang, common=True), reply_markup=reply_markup
    )


async def check_subscription_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, mongo_manager: MongoManager
):
    """Check user's subscription status"""
    user_info = mongo_manager.get_user_info(update)
    user_id = user_info["user_id"]
    lang = user_info["lang"]

    subscription = mongo_manager.get_subscription(user_id)
    if subscription.get("is_premium"):
        expiration = datetime.fromisoformat(subscription["premium_expiration"])
        remaining = (expiration - datetime.now()).days

        if remaining > 0:
            await update.message.reply_text(
                t("subscription.active", lang, common=True).format(
                    days=remaining,
                    date=expiration.strftime("%Y-%m-%d"),
                )
            )
        else:
            mongo_manager.update_subscription(user_id, {"is_premium": False})
            await update.message.reply_text(t("subscription.expired", lang))
    else:
        await update.message.reply_text(t("subscription.none", lang))
