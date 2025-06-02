import pytest

def test_required_constants_success(monkeypatch):
    """Test that no error is raised when all required constants are set."""
    # Set required environment variables
    monkeypatch.setenv("BOTS_AMOUNT", "5")
    
    # Import after setting environment variable
    from telegram_libs.constants import required_constants, missing_constants
    
    # Re-import the module to trigger the validation
    import importlib
    import telegram_libs.constants
    importlib.reload(telegram_libs.constants)

def test_required_constants_missing(monkeypatch):
    """Test that ValueError is raised when required constants are missing."""
    # Ensure the environment variable is not set
    monkeypatch.delenv("BOTS_AMOUNT", raising=False)
    
    # Import after removing environment variable
    import importlib
    import telegram_libs.constants
    
    with pytest.raises(ValueError) as exc_info:
        importlib.reload(telegram_libs.constants)
    
    assert "Required constants are not set: BOTS_AMOUNT" in str(exc_info.value) 