import os

os.environ["BOTS_AMOUNT"] = "5"
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["SUBSCRIPTION_DB_NAME"] = "subscription_db"

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update
from telegram.ext import ContextTypes
from telegram_libs.error import error_handler

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    return update

@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.error = Exception("Test error")
    return context

@pytest.mark.asyncio
async def test_error_handler(mock_update, mock_context):
    """Test that error_handler logs the error message."""
    with patch('telegram_libs.error.logger') as mock_logger:
        with patch('telegram_libs.error.BotLogger') as MockBotLogger:
            mock_bot_logger = MockBotLogger.return_value
            await error_handler(mock_update, mock_context, mock_bot_logger, "TestBot")
            mock_logger.error.assert_called_once_with(f"Update {mock_update} caused error {mock_context.error}")
            mock_bot_logger.log_action.assert_called_once_with(mock_update.effective_user.id, "error_handler", "TestBot", mock_context.error)