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
        await error_handler(mock_update, mock_context)
        mock_logger.error.assert_called_once_with(f"Update {mock_update} caused error {mock_context.error}") 