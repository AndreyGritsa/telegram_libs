from logging import getLogger
from telegram import Update
from telegram.ext import ContextTypes
from telegram_libs.logger import BotLogger

logger = getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_logger: BotLogger, bot_name: str) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    bot_logger.log_action(update.effective_user.id, "error_handler", bot_name, context.error)