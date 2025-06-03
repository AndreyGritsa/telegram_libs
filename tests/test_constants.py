import pytest

def test_required_constants_success(monkeypatch):
    """Test that no error is raised when all required constants are set."""
    # Set required environment variables
    monkeypatch.setenv("BOTS_AMOUNT", "5")
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("SUBSCRIPTION_DB_NAME", "subscription_db")
    
    # Import after setting environment variables
    from telegram_libs.constants import required_constants, missing_constants
    
    # Re-import the module to trigger the validation
    import importlib
    import telegram_libs.constants
    importlib.reload(telegram_libs.constants)

def test_required_constants_missing(monkeypatch):
    """Test that ValueError is raised when required constants are missing."""
    # Ensure the environment variables are not set
    monkeypatch.delenv("BOTS_AMOUNT", raising=False)
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("SUBSCRIPTION_DB_NAME", raising=False)
    
    # Import after removing environment variables
    import importlib
    import telegram_libs.constants
    
    with pytest.raises(ValueError) as exc_info:
        importlib.reload(telegram_libs.constants)
    
    error_message = str(exc_info.value)
    assert "Required constants are not set:" in error_message
    assert "BOTS_AMOUNT" in error_message
    assert "MONGO_URI" in error_message
    assert "SUBSCRIPTION_DB_NAME" in error_message

def test_required_constants_partial_missing(monkeypatch):
    """Test that ValueError is raised when some required constants are missing."""
    # Set only one environment variable
    monkeypatch.setenv("BOTS_AMOUNT", "5")
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("SUBSCRIPTION_DB_NAME", raising=False)
    
    # Import after setting/removing environment variables
    import importlib
    import telegram_libs.constants
    
    with pytest.raises(ValueError) as exc_info:
        importlib.reload(telegram_libs.constants)
    
    error_message = str(exc_info.value)
    assert "Required constants are not set:" in error_message
    assert "BOTS_AMOUNT" not in error_message  # This one is set
    assert "MONGO_URI" in error_message
    assert "SUBSCRIPTION_DB_NAME" in error_message 