from functools import partial
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    PreCheckoutQueryHandler,
)
from telegram_libs.mongo import MongoManager
from telegram_libs.subscription import subscription_callback, subscribe_command, check_subscription_command
from telegram_libs.payment import precheckout_handler, successful_payment
from telegram_libs.support import (
    handle_support_command,
    _handle_user_response,
    SupportFilter,
)
from telegram_libs.utils import more_bots_list_command
from telegram_libs.error import error_handler
from telegram_libs.logger import BotLogger


def register_subscription_handlers(
    app: Application, mongo_manager: MongoManager, bot_logger: BotLogger
) -> None:
    """Register subscription-related handlers."""
    app.add_handler(CallbackQueryHandler(partial(subscription_callback, bot_logger=bot_logger), pattern="^sub_"))
    app.add_handler(CommandHandler("subscribe", partial(subscribe_command, mongo_manager=mongo_manager, bot_logger=bot_logger)))
    app.add_handler(CommandHandler("status", partial(check_subscription_command, mongo_manager=mongo_manager)))

    # Payment handlers
    app.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, partial(successful_payment, mongo_manager=mongo_manager, bot_logger=bot_logger)))


def register_support_handlers(app: Application, bot_name: str, bot_logger: BotLogger) -> None:
    """Register support handlers for the bot"""
    app.add_handler(CommandHandler("support", partial(handle_support_command, bot_logger=bot_logger)))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & SupportFilter(),
            partial(_handle_user_response, bot_name=bot_name, bot_logger=bot_logger),
        )
    )


def register_common_handlers(
    app: Application, bot_name: str, mongo_manager: MongoManager
) -> None:
    """Register common handlers for the bot"""
    bot_logger = BotLogger()
    app.add_handler(CommandHandler("more", partial(more_bots_list_command, bot_logger=bot_logger)))
    
    register_support_handlers(app, bot_name, bot_logger)
    register_subscription_handlers(app, mongo_manager, bot_logger)
    
    # Error handler
    app.add_error_handler(partial(error_handler, bot_logger=bot_logger, bot_name=bot_name))
