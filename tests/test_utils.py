import os

# Set required environment variables
os.environ["BOTS_AMOUNT"] = "5"  
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["SUBSCRIPTION_DB_NAME"] = "subscription_db"

from datetime import datetime
from functools import partial
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call, ANY
from telegram import Update, Message
from telegram.ext import Application
from telegram_libs.utils import get_subscription_keyboard, t, RateLimitManager
from telegram_libs.constants import BOTS_AMOUNT, BOTS
from telegram_libs.support import handle_support_command, _handle_user_response, SUPPORT_WAITING
from telegram_libs.logger import BotLogger
from telegram_libs.error import error_handler
from telegram.ext import ContextTypes

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 123
    update.effective_user.language_code = 'en'
    return update

@pytest.mark.asyncio
async def test_get_subscription_keyboard_layout(mock_update):
    # Test with English language
    keyboard = await get_subscription_keyboard(mock_update, "en")
    
    # Check that reply_text was called with correct message
    mock_update.message.reply_text.assert_called_once_with(
        f"Buying a subscription you will get unlimited access to this one and to other {int(BOTS_AMOUNT) - 1} bots, to see all bots click /more"
    )
    
    # Check keyboard layout
    assert len(keyboard.inline_keyboard) == 2  # Two rows
    assert len(keyboard.inline_keyboard[0]) == 2  # First row has 2 buttons
    assert len(keyboard.inline_keyboard[1]) == 1  # Second row has 1 button
    
    # Check button texts and callback data
    assert keyboard.inline_keyboard[0][0].text == t("subscription.plans.1month", "en", common=True)
    assert keyboard.inline_keyboard[0][0].callback_data == "sub_1month"
    
    assert keyboard.inline_keyboard[0][1].text == t("subscription.plans.3months", "en", common=True)
    assert keyboard.inline_keyboard[0][1].callback_data == "sub_3months"
    
    assert keyboard.inline_keyboard[1][0].text == t("subscription.plans.1year", "en", common=True)
    assert keyboard.inline_keyboard[1][0].callback_data == "sub_1year"

@pytest.mark.asyncio
async def test_get_subscription_keyboard_different_language(mock_update):
    # Test with a different language
    keyboard = await get_subscription_keyboard(mock_update, "ru")
    
    # Check that reply_text was called with correct message
    mock_update.message.reply_text.assert_called_once_with(
        f"Купив подписку, вы получите неограниченный доступ к другим {int(BOTS_AMOUNT) - 1} ботам, чтобы увидеть всех ботов, нажмите /more"
    )
    
    # Check keyboard layout remains the same
    assert len(keyboard.inline_keyboard) == 2
    assert len(keyboard.inline_keyboard[0]) == 2
    assert len(keyboard.inline_keyboard[1]) == 1
    
    # Check callback data remains the same regardless of language
    assert keyboard.inline_keyboard[0][0].callback_data == "sub_1month"
    assert keyboard.inline_keyboard[0][1].callback_data == "sub_3months"
    assert keyboard.inline_keyboard[1][0].callback_data == "sub_1year"

@pytest.mark.asyncio
async def test_more_bots_list_command(mock_update):
    from telegram_libs.utils import more_bots_list_command
    
    # Create a mock context and bot_logger
    mock_context = MagicMock()
    mock_context.bot.name = "TestBot"
    mock_bot_logger = MagicMock(spec=BotLogger)
    
    # Call the function
    await more_bots_list_command(mock_update, mock_context, mock_bot_logger)
    
    # Check that reply_text was called with correct message and parameters
    expected_message = "Here is the list of all bots:\n\n" + "\n".join(
        f"- <a href='{url}'>{name}</a>" for url, name in BOTS.items()
    )
    mock_update.message.reply_text.assert_called_once_with(
        expected_message,
        disable_web_page_preview=True,
        parse_mode='HTML'
    )
    mock_bot_logger.log_action.assert_called_once_with(mock_update.effective_user.id, "more_bots_list_command", "TestBot")

@pytest.mark.asyncio
async def test_support_command(mock_update):
    """Test the support_command handler."""
    from telegram_libs.logger import BotLogger
    mock_context = MagicMock()
    mock_context.user_data = {}
    mock_context.bot.name = "TestBot"
    mock_bot_logger = MagicMock(spec=BotLogger)

    await handle_support_command(mock_update, mock_context, mock_bot_logger)
    
    mock_update.message.reply_text.assert_called_once_with(
        t("support.message", mock_update.effective_user.language_code, common=True)
    )
    assert mock_context.user_data[SUPPORT_WAITING] is True
    mock_bot_logger.log_action.assert_called_once_with(mock_update.effective_user.id, "support_command", "TestBot")

@pytest.mark.asyncio
async def test_handle_support_response(mock_update):
    """Test the handle_support_response handler."""
    from telegram_libs.logger import BotLogger
    mock_context = MagicMock()
    mock_context.user_data = {SUPPORT_WAITING: True}
    mock_update.effective_user.id = 123
    mock_update.effective_user.username = "testuser"
    mock_update.message.text = "This is a support message."
    mock_update.message.date = datetime.now()
    mock_context.bot.name = "TestBot"
    mock_bot_logger = MagicMock(spec=BotLogger)
    
    # Define a fixed datetime for consistent testing
    fixed_now = datetime(2024, 1, 1, 10, 0, 0)

    mock_support_collection = MagicMock()
    # Patch the mongo_client to return our mock collection
    with patch('telegram_libs.support.mongo_manager_instance.client') as mock_mongo_client, \
         patch('telegram_libs.support.datetime') as mock_dt: # Patch datetime in support_handlers
        mock_mongo_client.__getitem__.return_value.__getitem__.return_value = mock_support_collection
        mock_dt.now.return_value = fixed_now # Set fixed time for datetime.now()
        mock_dt.isoformat.side_effect = fixed_now.isoformat # Ensure isoformat also works

        await _handle_user_response(mock_update, mock_context, "TestBot", mock_bot_logger)
    
    mock_support_collection.insert_one.assert_called_once_with({
        "user_id": 123,
        "username": "testuser",
        "message": "This is a support message.",
        "bot_name": "TestBot",
        "timestamp": fixed_now.isoformat(), # Use the fixed timestamp for assertion
        "resolved": False,
    })
    mock_update.message.reply_text.assert_called_once_with(
        t("support.response", mock_update.effective_user.language_code, common=True)
    )
    assert mock_context.user_data[SUPPORT_WAITING] is False
    mock_bot_logger.log_action.assert_called_once_with(mock_update.effective_user.id, "support_message_sent", "TestBot", {"message": "This is a support message."})

@pytest.mark.asyncio
async def test_handle_support_response_not_waiting(mock_update):
    """Test handle_support_response when not in waiting state."""
    from telegram_libs.logger import BotLogger
    mock_context = MagicMock()
    mock_context.user_data = {SUPPORT_WAITING: False}
    mock_context.bot.name = "TestBot"
    mock_bot_logger = MagicMock(spec=BotLogger)
    
    # Patch the mongo_client to ensure it's not called
    with patch('telegram_libs.support.mongo_manager_instance.client') as mock_mongo_client:
        await _handle_user_response(mock_update, mock_context, "TestBot", mock_bot_logger)
        mock_mongo_client.__getitem__.assert_not_called()

    mock_update.message.reply_text.assert_not_called()
    assert mock_context.user_data[SUPPORT_WAITING] is False
    mock_bot_logger.log_action.assert_not_called()

@pytest.fixture
def mock_application():
    app = MagicMock(spec=Application)
    app.add_handler = MagicMock()
    return app

def test_register_common_handlers(mock_application):
    """Test registration of common handlers."""
    from telegram_libs.handlers import register_common_handlers
    from telegram_libs.utils import more_bots_list_command
    from telegram.ext import CommandHandler
    from telegram_libs.support import register_support_handlers
    from telegram_libs.mongo import MongoManager
    from unittest.mock import patch, MagicMock

    mock_mongo_manager = MagicMock(spec=MongoManager)

    with patch('telegram_libs.handlers.register_support_handlers') as mock_register_support_handlers, \
         patch('telegram_libs.handlers.register_subscription_handlers') as mock_register_subscription_handlers, \
         patch('telegram_libs.handlers.BotLogger') as MockBotLogger,\
         patch.object(mock_application, 'add_error_handler') as mock_add_error_handler:

        mock_bot_logger_instance = MockBotLogger.return_value
        register_common_handlers(mock_application, "TestBot", mock_mongo_manager)
        
        calls = mock_application.add_handler.call_args_list
        assert len(calls) == 1
        assert isinstance(calls[0].args[0], CommandHandler)
        assert "more" in calls[0].args[0].commands
        
        # Assert that the callback is a partial object and its function is more_bots_list_command
        # and that bot_logger is correctly passed
        assert isinstance(calls[0].args[0].callback, partial)
        assert calls[0].args[0].callback.func == more_bots_list_command
        assert calls[0].args[0].callback.keywords == {'bot_logger': mock_bot_logger_instance}

        # Assert that add_error_handler was called with partial(error_handler, ...)
        mock_add_error_handler.assert_called_once()
        call_args, call_kwargs = mock_add_error_handler.call_args
        assert isinstance(call_args[0], partial)
        assert call_args[0].func == error_handler
        assert call_args[0].keywords == {'bot_logger': mock_bot_logger_instance, 'bot_name': "TestBot"}

        mock_register_support_handlers.assert_called_once_with(mock_application, "TestBot", mock_bot_logger_instance)
        mock_register_subscription_handlers.assert_called_once_with(mock_application, mock_mongo_manager, mock_bot_logger_instance)

@pytest.mark.asyncio
async def test_support_filter_true(mock_update):
    """Test SupportFilter returns True when SUPPORT_WAITING is True."""
    from telegram_libs.support import SupportFilter, SUPPORT_WAITING
    mock_context = MagicMock()
    mock_context.user_data = {SUPPORT_WAITING: True}
    
    support_filter = SupportFilter()
    result = support_filter(mock_update, mock_context)
    
    assert result is True

@pytest.mark.asyncio
async def test_support_filter_false(mock_update):
    """Test SupportFilter returns False when SUPPORT_WAITING is False."""
    from telegram_libs.support import SupportFilter, SUPPORT_WAITING
    mock_context = MagicMock()
    mock_context.user_data = {SUPPORT_WAITING: False}
    
    support_filter = SupportFilter()
    result = support_filter(mock_update, mock_context)
    
    assert result is False

@pytest.mark.asyncio
async def test_support_filter_no_key(mock_update):
    """Test SupportFilter returns False when SUPPORT_WAITING key is not present."""
    from telegram_libs.support import SupportFilter
    mock_context = MagicMock()
    mock_context.user_data = {}
    
    support_filter = SupportFilter()
    result = support_filter(mock_update, mock_context)
    
    assert result is False

class TestRateLimitManager:
    @pytest.fixture
    def mock_mongo_manager(self):
        manager = MagicMock()
        manager.get_user_data.return_value = {}
        manager.check_subscription_status.return_value = False # Default for non-premium tests
        return manager

    @pytest.fixture
    def mock_context(self):
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        return context

    @pytest.fixture
    def rate_limit_manager(self, mock_mongo_manager):
        return RateLimitManager(mongo_manager=mock_mongo_manager, rate_limit=3)

    def test_init(self, mock_mongo_manager):
        manager = RateLimitManager(mock_mongo_manager, rate_limit=5)
        assert manager.mongo_manager == mock_mongo_manager
        assert manager.rate_limit == 5

    @patch("telegram_libs.utils.datetime")
    def test_check_limit_first_action_today(self, mock_datetime, rate_limit_manager, mock_mongo_manager):
        user_id = 123
        
        mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0) # Mock datetime.now() to return a specific datetime
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x) # Allow real fromisoformat to be called

        # Mock user data as if no previous action date
        mock_mongo_manager.get_user_data.return_value = {"actions_today": 0, "last_action_date": None}
        
        can_perform, _ = rate_limit_manager.check_limit(user_id)
        assert can_perform is True
        mock_mongo_manager.get_user_data.assert_called_once_with(user_id)
        mock_mongo_manager.update_user_data.assert_not_called()

    @patch("telegram_libs.utils.datetime")
    def test_check_limit_within_limit_same_day(self, mock_datetime, rate_limit_manager, mock_mongo_manager):
        user_id = 123
        
        # Mock datetime.now() and datetime.fromisoformat() to return datetimes on the same day
        mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x) # Allow real fromisoformat to be called

        mock_user_data = {
            "last_action_date": "2024-01-01T09:00:00", # Should be the same date as mock_now
            "actions_today": 2  # Within limit of 3
        }
        mock_mongo_manager.get_user_data.return_value = mock_user_data
        
        can_perform, _ = rate_limit_manager.check_limit(user_id)
        assert can_perform is True
        mock_mongo_manager.get_user_data.assert_called_once_with(user_id)
        mock_mongo_manager.update_user_data.assert_not_called()

    @patch("telegram_libs.utils.datetime")
    def test_check_limit_new_day_resets_count(self, mock_datetime, rate_limit_manager, mock_mongo_manager):
        user_id = 123
        
        # Mock datetime.now() to be a new day, and datetime.fromisoformat() to be the previous day
        mock_datetime.now.return_value = datetime(2024, 1, 2, 10, 0, 0)
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x) # Allow real fromisoformat to be called

        mock_user_data = {
            "last_action_date": "2024-01-01T15:00:00",
            "actions_today": 5  # Exceeded yesterday
        }
        mock_mongo_manager.get_user_data.return_value = mock_user_data
        
        can_perform, _ = rate_limit_manager.check_limit(user_id)
        assert can_perform is True
        mock_mongo_manager.get_user_data.assert_called_once_with(user_id)
        mock_mongo_manager.update_user_data.assert_called_once_with(
            user_id,
            {
                "actions_today": 0,
                "last_action_date": datetime(2024, 1, 2, 10, 0, 0).isoformat(),
            },
        )

    @patch("telegram_libs.utils.datetime")
    def test_check_limit_exceeded(self, mock_datetime, rate_limit_manager, mock_mongo_manager):
        user_id = 123

        # Mock datetime.now() and datetime.fromisoformat() to be the same day
        mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x) # Allow real fromisoformat to be called

        mock_user_data = {
            "last_action_date": "2024-01-01T09:00:00",
            "actions_today": 3  # At the limit of 3
        }
        mock_mongo_manager.get_user_data.return_value = mock_user_data

        can_perform, _ = rate_limit_manager.check_limit(user_id)
        assert can_perform is False
        mock_mongo_manager.get_user_data.assert_called_once_with(user_id)
        mock_mongo_manager.update_user_data.assert_not_called()

    @patch("telegram_libs.utils.datetime")
    def test_increment_action_count(self, mock_datetime, rate_limit_manager, mock_mongo_manager):
        user_id = 123
        initial_actions = 2
        mock_user_data = {"actions_today": initial_actions, "last_action_date": "2024-01-01T09:00:00"}
        mock_mongo_manager.get_user_data.return_value = mock_user_data
        
        fixed_now = datetime(2024, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = fixed_now
        # mock_datetime.isoformat.side_effect = fixed_now.isoformat # Not needed if datetime.now() returns real datetime object

        rate_limit_manager.increment_action_count(user_id, mock_user_data)
        
        mock_mongo_manager.get_user_data.assert_not_called() # Should not be called if user_data is provided
        mock_mongo_manager.update_user_data.assert_called_once_with(
            user_id,
            {"actions_today": initial_actions + 1, "last_action_date": fixed_now.isoformat()},
        )

    @patch("telegram_libs.utils.datetime")
    def test_check_and_increment_premium_user(self, mock_datetime, rate_limit_manager, mock_mongo_manager):
        user_id = 123
        mock_mongo_manager.check_subscription_status.return_value = True

        result = rate_limit_manager.check_and_increment(user_id)

        assert result is True
        mock_mongo_manager.check_subscription_status.assert_called_once_with(user_id)
        mock_mongo_manager.get_user_data.assert_not_called() # Should not be called for premium users
        mock_mongo_manager.update_user_data.assert_not_called() # Should not be called for premium users

    @patch("telegram_libs.utils.datetime")
    def test_check_and_increment_non_premium_within_limit(self, mock_datetime, rate_limit_manager, mock_mongo_manager):
        user_id = 123
        mock_mongo_manager.check_subscription_status.return_value = False

        fixed_now = datetime(2024, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x) # Allow real fromisoformat to be called

        mock_user_data = {
            "last_action_date": "2024-01-01T09:00:00",
            "actions_today": 2  # Within limit of 3
        }
        mock_mongo_manager.get_user_data.return_value = mock_user_data

        result = rate_limit_manager.check_and_increment(user_id)

        assert result is True
        mock_mongo_manager.check_subscription_status.assert_called_once_with(user_id)
        mock_mongo_manager.get_user_data.assert_called_once_with(user_id)
        mock_mongo_manager.update_user_data.assert_called_once_with(
            user_id,
            {"actions_today": 3, "last_action_date": fixed_now.isoformat()},
        )

    @patch("telegram_libs.utils.datetime")
    def test_check_and_increment_non_premium_exceeded_limit(self, mock_datetime, rate_limit_manager, mock_mongo_manager):
        user_id = 123
        mock_mongo_manager.check_subscription_status.return_value = False

        fixed_now = datetime(2024, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x) # Allow real fromisoformat to be called

        mock_user_data = {
            "last_action_date": "2024-01-01T09:00:00",
            "actions_today": 3  # At the limit of 3
        }
        mock_mongo_manager.get_user_data.return_value = mock_user_data

        result = rate_limit_manager.check_and_increment(user_id)

        assert result is False
        mock_mongo_manager.check_subscription_status.assert_called_once_with(user_id)
        mock_mongo_manager.get_user_data.assert_called_once_with(user_id)
        mock_mongo_manager.update_user_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_limit_with_response_within_limit(self, mock_update, mock_context, rate_limit_manager, mock_mongo_manager):
        user_id = mock_update.effective_user.id
        # Mock check_and_increment to return True (within limit or premium)
        with patch.object(rate_limit_manager, "check_and_increment", return_value=True) as mock_check_and_increment:
            result = await rate_limit_manager.check_limit_with_response(mock_update, mock_context, user_id)

            mock_check_and_increment.assert_called_once_with(user_id)
            mock_update.message.reply_text.assert_not_called()
            # Ensure get_subscription_keyboard was not called
            with patch("telegram_libs.utils.get_subscription_keyboard") as mock_get_subscription_keyboard:
                mock_get_subscription_keyboard.assert_not_called()
            assert result is True

    @pytest.mark.asyncio
    async def test_check_limit_with_response_exceeded_limit(self, mock_update, mock_context, rate_limit_manager, mock_mongo_manager):
        user_id = mock_update.effective_user.id
        lang_code = "en"
        # Mock check_and_increment to return False (exceeded limit and not premium)
        with patch.object(rate_limit_manager, "check_and_increment", return_value=False) as mock_check_and_increment, \
             patch("telegram_libs.utils.get_subscription_keyboard") as mock_get_subscription_keyboard:
            
            mock_mongo_manager.get_user_info.return_value = {"lang": lang_code}

            result = await rate_limit_manager.check_limit_with_response(mock_update, mock_context, user_id)

            mock_check_and_increment.assert_called_once_with(user_id)
            mock_mongo_manager.get_user_info.assert_called_once_with(mock_update)

            expected_calls = [
                call(t("rate_limit.exceeded", lang_code, common=True)),
                call(t("subscription.choose_plan", lang_code, common=True), reply_markup=ANY)
            ]
            mock_update.message.reply_text.assert_has_calls(expected_calls)
            mock_get_subscription_keyboard.assert_called_once_with(mock_update, lang_code)
            assert result is False