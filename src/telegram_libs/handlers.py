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


def register_subscription_handlers(
    app: Application, mongo_manager: MongoManager
) -> None:
    """Register subscription-related handlers."""
    app.add_handler(CallbackQueryHandler(subscription_callback, pattern="^sub_"))
    app.add_handler(CommandHandler("subscribe", partial(subscribe_command, mongo_manager=mongo_manager)))
    app.add_handler(CommandHandler("status", partial(check_subscription_command, mongo_manager=mongo_manager)))

    # Payment handlers
    app.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, partial(successful_payment, mongo_manager=mongo_manager)))


def register_support_handlers(app: Application, bot_name: str) -> None:
    """Register support handlers for the bot"""
    app.add_handler(CommandHandler("support", handle_support_command))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & SupportFilter(),
            partial(_handle_user_response, bot_name=bot_name),
        )
    )


def register_common_handlers(
    app: Application, bot_name: str, mongo_manager: MongoManager
) -> None:
    """Register common handlers for the bot"""
    app.add_handler(CommandHandler("more", more_bots_list_command))
    
    register_support_handlers(app, bot_name)
    register_subscription_handlers(app, mongo_manager)
    
    # Error handler
    app.add_error_handler(error_handler)
