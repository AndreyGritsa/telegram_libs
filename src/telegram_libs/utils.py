from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters
from telegram_libs.constants import BOTS_AMOUNT
from telegram_libs.translation import t
from telegram_libs.mongo import mongo_client
from functools import partial

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
        f"Buying a subscription you will get unlimited access to other {int(BOTS_AMOUNT) - 1} bots, to see all bots click /more"
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
    

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Support command handler"""
    await update.message.reply_text(
        "If you have any questions or need help, please contact our support team at @support_channel."
    )
    context.user_data[SUPPORT_WAITING] = True
    

async def handle_support_response(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_name: str) -> None:
    """Handle user's support message"""
    if context.user_data.get(SUPPORT_WAITING):
        support_db = mongo_client["support"]
        support_collection = support_db["support"]
        support_doc = {
            "user_id": update.effective_user.id,
            "username": update.effective_user.username,
            "message": update.message.text,
            "bot_name": bot_name,
        }
        support_collection.insert_one(support_doc)
        await update.message.reply_text("Thank you! Our support team will contact you soon.")
        context.user_data[SUPPORT_WAITING] = False
    

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Feedback command handler"""
    await update.message.reply_text(
        "We appreciate your feedback! Please send your suggestions or issues and we will review them as soon as possible."
    )
    context.user_data[FEEDBACK_WAITING] = True
 
    
async def handle_feedback_response(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_name: str) -> None:
    """Handle user's feedback message"""
    if context.user_data.get(FEEDBACK_WAITING):
        feedback_db = mongo_client["feedback"]
        feedback_collection = feedback_db["feedback"]
        feedback_doc = {
            "user_id": update.effective_user.id,
            "username": update.effective_user.username,
            "feedback": update.message.text,
            "bot_name": bot_name,
        }
        feedback_collection.insert_one(feedback_doc)
        await update.message.reply_text("Thank you for your feedback!")
        context.user_data[FEEDBACK_WAITING] = False
        
        
def register_feedback_and_support_handlers(app: Application, bot_name: str) -> None:
    """Register feedback and support handlers for the bot"""
    app.add_handler(CommandHandler("feedback", feedback_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, partial(handle_feedback_response, bot_name=bot_name)))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, partial(handle_support_response, bot_name=bot_name)))


def register_common_handlers(app: Application, bot_name: str) -> None:
    """Register common handlers for the bot"""
    app.add_handler(CommandHandler("more", more_bots_list_command))
    register_feedback_and_support_handlers(app, bot_name)