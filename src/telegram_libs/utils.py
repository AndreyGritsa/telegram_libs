from functools import partial
from logging import basicConfig, getLogger, INFO
from datetime import datetime
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters
from telegram.ext.filters import BaseFilter
from telegram_libs.constants import BOTS_AMOUNT
from telegram_libs.translation import t
from telegram_libs.mongo import mongo_client



basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=INFO
)
logger = getLogger(__name__)


FEEDBACK_WAITING = "feedback_waiting"
SUPPORT_WAITING = "support_waiting"


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
    message = """Here is the list of all bots: \n\n
    - <a href="https://t.me/MagMediaBot">Remove Background</a>
    - <a href="https://t.me/UpscaleImageGBot">Upscale Image</a>
    - <a href="https://t.me/GenerateBackgroundGBot">Generate a Background</a>
    - <a href="https://t.me/kudapoyti_go_bot">Recommend a place to visit</a>
    - <a href="https://t.me/TryOnOutfitGBot">Try On Outfit</a>
    """
    await update.message.reply_text(message, disable_web_page_preview=True, parse_mode='HTML')
    

async def handle_support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Support command handler"""
    await update.message.reply_text(
        t("support.message", update.effective_user.language_code, common=True)
    )
    context.user_data[SUPPORT_WAITING] = True
    

async def _handle_user_response(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_name: str) -> None:
    """Handle user's support or feedback message"""
    if context.user_data.get(FEEDBACK_WAITING):
        db_name = "feedback"
        collection_name = "feedback"
        message_key = "feedback.response"
        doc_field_name = "feedback"
        context_key = FEEDBACK_WAITING
        extra_fields = {}
    elif context.user_data.get(SUPPORT_WAITING):
        db_name = "support"
        collection_name = "support"
        message_key = "support.response"
        doc_field_name = "message"
        context_key = SUPPORT_WAITING
        extra_fields = {"resolved": False}
    else:
        # Should not happen if filter is correct
        return

    db = mongo_client[db_name]
    collection = db[collection_name]
    doc = {
        "user_id": update.effective_user.id,
        "username": update.effective_user.username,
        doc_field_name: update.message.text,
        "bot_name": bot_name,
        "timestamp": datetime.now().isoformat(),
    }
    doc.update(extra_fields)
    collection.insert_one(doc)
    await update.message.reply_text(t(message_key, update.effective_user.language_code, common=True))
    context.user_data[context_key] = False


async def handle_feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Feedback command handler"""
    await update.message.reply_text(
        t("feedback.message", update.effective_user.language_code, common=True)
    )
    context.user_data[FEEDBACK_WAITING] = True


class CombinedFeedbackSupportFilter(BaseFilter):
    def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return context.user_data.get(FEEDBACK_WAITING, False) or context.user_data.get(SUPPORT_WAITING, False)


def register_feedback_and_support_handlers(app: Application, bot_name: str) -> None:
    """Register feedback and support handlers for the bot"""
    app.add_handler(CommandHandler("feedback", handle_feedback_command))
    app.add_handler(CommandHandler("support", handle_support_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & CombinedFeedbackSupportFilter(), partial(_handle_user_response, bot_name=bot_name)))


def register_common_handlers(app: Application, bot_name: str) -> None:
    """Register common handlers for the bot"""
    app.add_handler(CommandHandler("more", more_bots_list_command))
    register_feedback_and_support_handlers(app, bot_name)