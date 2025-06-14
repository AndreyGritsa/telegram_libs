from logging import basicConfig, getLogger, INFO
from datetime import datetime
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram import Update
from telegram.ext import ContextTypes
from telegram_libs.constants import BOTS, BOTS_AMOUNT
from telegram_libs.translation import t
from telegram_libs.mongo import MongoManager
from telegram_libs.logger import BotLogger



basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=INFO
)
logger = getLogger(__name__)


async def get_subscription_keyboard(update: Update, lang: str) -> InlineKeyboardMarkup:
    """Get subscription keyboard

    Args:
        update (Update): Update object
        lang (str): Language code

    Returns:
        InlineKeyboardMarkup: Inline keyboard markup
    """
    await update.message.reply_text(
        t("subscription.info", lang, common=True).format(BOTS_AMOUNT - 1)
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
    

async def more_bots_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_logger: BotLogger) -> None:
    user_id = update.effective_user.id
    bot_name = context.bot.name
    bot_logger.log_action(user_id, "more_bots_list_command", bot_name)
    message = "Here is the list of all bots:\n\n"
    bots_list  = "\n".join(
        f"- <a href='{url}'>{name}</a>" for url, name in BOTS.items()
    )
    message += bots_list
    await update.message.reply_text(message, disable_web_page_preview=True, parse_mode='HTML')
    
    
class RateLimitManager:
    """Rate limit manager to handle user rate limits."""
    
    def __init__(self, mongo_manager: MongoManager, rate_limit: int = 5):
        self.mongo_manager = mongo_manager
        self.rate_limit = rate_limit

    def check_limit(self, user_id: int) -> tuple[bool, dict]:
        """Check if user has exceeded the daily rate limit."""
        # Get today's date and reset time to midnight
        today = datetime.now().date()

        # If last action date is not today, reset the counter
        user_data = self.mongo_manager.get_user_data(user_id)
        last_action_date_str = user_data.get("last_action_date")
        if last_action_date_str:
            last_action_date = datetime.fromisoformat(last_action_date_str).date()
            if last_action_date != today:
                self.mongo_manager.update_user_data(
                    user_id,
                    {
                        "actions_today": 0,
                        "last_action_date": datetime.now().isoformat(),
                    },
                )
                user_data["actions_today"] = 0
                user_data["last_action_date"] = datetime.now().isoformat()
                return True, user_data

        # Check if user has exceeded the limit
        actions_today = user_data.get("actions_today", 0)
        if actions_today >= self.rate_limit:
            return False, user_data

        return True, user_data
    
    def check_and_increment(self, user_id: int) -> bool:
        """Check if user can perform an action and increment the count if allowed."""
        if self.mongo_manager.check_subscription_status(user_id):
            return True

        can_perform, user_data = self.check_limit(user_id)
        if can_perform:
            self.increment_action_count(user_id, user_data)
            return True
        return False
    
    async def check_limit_with_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
        """Check if user can perform an action and handle the response."""
        if not self.check_and_increment(user_id):
            lang = self.mongo_manager.get_user_info(update).get("lang")
            message = t("rate_limit.exceeded", lang, common=True)
            await update.message.reply_text(message)
            reply_markup = await get_subscription_keyboard(update, lang)
            await update.message.reply_text(
                t("subscription.choose_plan", lang, common=True), reply_markup=reply_markup
            )
            return False
        return True

    def increment_action_count(self, user_id: int, user_data: dict = None) -> None:
        """Increment the daily action count for the user."""
        if user_data is None:
            user_data = self.mongo_manager.get_user_data(user_id)
        current_actions = user_data.get("actions_today", 0)
        self.mongo_manager.update_user_data(
            user_id,
            {"actions_today": current_actions + 1, "last_action_date": datetime.now().isoformat()},
        )
