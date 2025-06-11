from functools import partial
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters
from telegram.ext.filters import BaseFilter
from telegram_libs.mongo import MongoManager
from telegram_libs.constants import DEBUG, SUBSCRIPTION_DB_NAME
from telegram_libs.translation import t
from telegram_libs.logger import BotLogger


SUPPORT_WAITING = "support_waiting"

mongo_manager_instance = MongoManager(mongo_database_name=SUBSCRIPTION_DB_NAME) # Use an existing or create a new MongoManager instance


async def handle_support_command(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_logger: BotLogger) -> None:
    """Support command handler"""
    user_id = update.effective_user.id
    bot_name = context.bot.name
    bot_logger.log_action(user_id, "support_command", bot_name)
    await update.message.reply_text(
        t("support.message", update.effective_user.language_code, common=True)
    )
    context.user_data[SUPPORT_WAITING] = True
    

async def _handle_user_response(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_name: str, bot_logger: BotLogger) -> None:
    """Handle user's support message"""
    user_id = update.effective_user.id
    if context.user_data.get(SUPPORT_WAITING):
        bot_logger.log_action(user_id, "support_message_sent", bot_name, {"message": update.message.text})
        db_name = "support"
        collection_name = "support" if not DEBUG else "support_test"
        message_key = "support.response"
        doc_field_name = "message"
        context_key = SUPPORT_WAITING
        extra_fields = {"resolved": False}
    else:
        # Should not happen if filter is correct
        return

    db = mongo_manager_instance.client[db_name]
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


def register_support_handlers(application: Application, bot_name: str):
    application.add_handler(CommandHandler("support", handle_support_command))
    application.add_handler(
        MessageHandler(SupportFilter() & filters.TEXT, partial(_handle_user_response, bot_name=bot_name))
    )