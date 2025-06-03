from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram import Update
from telegram.ext import ContextTypes
from telegram_libs.constants import BOTS_AMOUNT
from telegram_libs.translation import t


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
                t("subscription.plans.1month", lang), callback_data="sub_1month"
            ),
            InlineKeyboardButton(
                t("subscription.plans.3months", lang), callback_data="sub_3months"
            ),
        ],
        [
            InlineKeyboardButton(
                t("subscription.plans.1year", lang), callback_data="sub_1year"
            ),
        ],
    ]
    

async def more_bots_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = """Here is the list of all bots: \n\n
    - <a href="https://t.me/MagMediaBot">Remove Background</a>
    - <a href="https://t.me/UpscaleImageGBot">Upscale Image</a>
    - <a href="https://t.me/kudapoyti_go_bot">Recommend a place to visit</a>
    """
    await update.message.reply_text(message, disable_web_page_preview=True, parse_mode='HTML')