from functools import partial
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters
from telegram.ext.filters import BaseFilter
from telegram_libs.mongo import mongo_client
from telegram_libs.constants import DEBUG
from telegram_libs.translation import t


SUPPORT_WAITING = "support_waiting"


async def handle_support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Support command handler"""
    await update.message.reply_text(
        t("support.message", update.effective_user.language_code, common=True)
    )
    context.user_data[SUPPORT_WAITING] = True
    

async def _handle_user_response(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_name: str) -> None:
    """Handle user's support message"""
    if context.user_data.get(SUPPORT_WAITING):
        db_name = "support"
        collection_name = "support" if not DEBUG else "support_test"
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


class SupportFilter(BaseFilter):
    def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return context.user_data.get(SUPPORT_WAITING, False)


def register_support_handlers(app: Application, bot_name: str) -> None:
    """Register support handlers for the bot"""
    app.add_handler(CommandHandler("support", handle_support_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & SupportFilter(), partial(_handle_user_response, bot_name=bot_name))) 