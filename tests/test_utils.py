import os
os.environ["BOTS_AMOUNT"] = "5"  # Set required environment variable

import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message, Chat
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
        f"Buying a subscription you will get unlimited access to other {BOTS_AMOUNT} bots, to see all bots click /more"
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
        f"Buying a subscription you will get unlimited access to other {BOTS_AMOUNT} bots, to see all bots click /more"
    )
    
    # Check keyboard layout remains the same
    assert len(keyboard) == 2
    assert len(keyboard[0]) == 2
    assert len(keyboard[1]) == 1
    
    # Check callback data remains the same regardless of language
    assert keyboard[0][0].callback_data == "sub_1month"
    assert keyboard[0][1].callback_data == "sub_3months"
    assert keyboard[1][0].callback_data == "sub_1year" 