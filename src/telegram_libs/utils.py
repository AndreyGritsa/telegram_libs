from logging import basicConfig, getLogger, INFO
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler, CallbackQueryHandler
from telegram_libs.constants import BOTS_AMOUNT
from telegram_libs.translation import t
from telegram_libs.support import register_support_handlers
from telegram_libs.mongo import MongoManager


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
        t("subscription.info", lang, common=True).format(int(BOTS_AMOUNT) - 1)
    )
    return [
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
    ]
    

async def more_bots_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = """Here is the list of all bots: 


    - <a href="https://t.me/MagMediaBot">Remove Background</a>
    - <a href="https://t.me/UpscaleImageGBot">Upscale Image</a>
    - <a href="https://t.me/GenerateBackgroundGBot">Generate a Background</a>
    - <a href="https://t.me/kudapoyti_go_bot">Recommend a place to visit</a>
    - <a href="https://t.me/TryOnOutfitGBot">Try On Outfit</a>
    """
    await update.message.reply_text(message, disable_web_page_preview=True, parse_mode='HTML')
    
    
def get_user_info(update: Update, mongo_manager: MongoManager) -> dict:
    """Get user information from the update object."""
    user = update.effective_user
    user_data = mongo_manager.get_user_data(user.id)
    
    return {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "lang": user_data.get("language", "en"),
        **user_data,
    }

def register_common_handlers(application: Application, bot_name: str) -> None:
    """Register common handlers to the application."""
    application.add_handler(CommandHandler("more", more_bots_list_command))
    register_support_handlers(application, bot_name)
