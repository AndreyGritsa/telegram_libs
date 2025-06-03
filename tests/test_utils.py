import os

# Set required environment variables
os.environ["BOTS_AMOUNT"] = "5"  
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["SUBSCRIPTION_DB_NAME"] = "subscription_db"

import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message
from telegram_libs.utils import get_subscription_keyboard
from telegram_libs.constants import BOTS_AMOUNT

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update

@pytest.mark.asyncio
async def test_get_subscription_keyboard_layout(mock_update):
    # Test with English language
    keyboard = await get_subscription_keyboard(mock_update, "en")
    
    # Check that reply_text was called with correct message
    mock_update.message.reply_text.assert_called_once_with(
        f"Buying a subscription you will get unlimited access to other {int(BOTS_AMOUNT) - 1} bots, to see all bots click /more"
    )
    
    # Check keyboard layout
    assert len(keyboard) == 2  # Two rows
    assert len(keyboard[0]) == 2  # First row has 2 buttons
    assert len(keyboard[1]) == 1  # Second row has 1 button
    
    # Check button texts and callback data
    assert keyboard[0][0].text == "subscription.plans.1month"
    assert keyboard[0][0].callback_data == "sub_1month"
    
    assert keyboard[0][1].text == "subscription.plans.3months"
    assert keyboard[0][1].callback_data == "sub_3months"
    
    assert keyboard[1][0].text == "subscription.plans.1year"
    assert keyboard[1][0].callback_data == "sub_1year"

@pytest.mark.asyncio
async def test_get_subscription_keyboard_different_language(mock_update):
    # Test with a different language
    keyboard = await get_subscription_keyboard(mock_update, "ru")
    
    # Check that reply_text was called with correct message
    mock_update.message.reply_text.assert_called_once_with(
        f"Buying a subscription you will get unlimited access to other {int(BOTS_AMOUNT) - 1} bots, to see all bots click /more"
    )
    
    # Check keyboard layout remains the same
    assert len(keyboard) == 2
    assert len(keyboard[0]) == 2
    assert len(keyboard[1]) == 1
    
    # Check callback data remains the same regardless of language
    assert keyboard[0][0].callback_data == "sub_1month"
    assert keyboard[0][1].callback_data == "sub_3months"
    assert keyboard[1][0].callback_data == "sub_1year"

@pytest.mark.asyncio
async def test_more_bots_list_command(mock_update):
    from telegram_libs.utils import more_bots_list_command
    
    # Create a mock context
    mock_context = MagicMock()
    
    # Call the function
    await more_bots_list_command(mock_update, mock_context)
    
    # Check that reply_text was called with correct message and parameters
    expected_message = """Here is the list of all bots: \n\n
    - <a href="https://t.me/MagMediaBot">Remove Background</a>
    - <a href="https://t.me/UpscaleImageGBot">Upscale Image</a>
    - <a href="https://t.me/kudapoyti_go_bot">Recommend a place to visit</a>
    """
    mock_update.message.reply_text.assert_called_once_with(
        expected_message,
        disable_web_page_preview=True,
        parse_mode='HTML'
    ) 