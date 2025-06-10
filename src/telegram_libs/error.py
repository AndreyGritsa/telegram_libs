from logging import getLogger
from telegram import Update
from telegram.ext import ContextTypes

logger = getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")