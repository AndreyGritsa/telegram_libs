import json
import pytest
from telegram_libs import translation

@pytest.fixture
def temp_locales_dir(tmp_path):
    """Create a temporary locales directory with test translation files"""
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()
    
    # Create test translation files
    en_translations = {
        "welcome": "Welcome",
        "buttons": {
            "start": "Start",
            "help": "Help"
        },
        "formatted": "Hello, {name}!"
    }
    
    ru_translations = {
        "welcome": "Добро пожаловать",
        "buttons": {
            "start": "Старт",
            "help": "Помощь"
        },
        "formatted": "Привет, {name}!"
    }
    
    # Write translation files
    with open(locales_dir / "en.json", "w", encoding="utf-8") as f:
        json.dump(en_translations, f)
    
    with open(locales_dir / "ru.json", "w", encoding="utf-8") as f:
        json.dump(ru_translations, f)
    
    return locales_dir

@pytest.fixture(autouse=True)
def reload_translations(temp_locales_dir, monkeypatch):
    """Reload translations before each test"""
    monkeypatch.chdir(temp_locales_dir.parent)
    translation.TRANSLATIONS = translation.load_translations()
    yield
    # Reset translations after test
    translation.TRANSLATIONS = {}

def test_load_translations(temp_locales_dir, monkeypatch):
    """Test loading translations from the locales directory"""
    translations = translation.load_translations()
    
    assert "en" in translations
    assert "ru" in translations
    assert translations["en"]["welcome"] == "Welcome"
    assert translations["ru"]["welcome"] == "Добро пожаловать"

def test_translation_simple():
    """Test simple translation without formatting"""
    assert translation.t("welcome", "en") == "Welcome"
    assert translation.t("welcome", "ru") == "Добро пожаловать"

def test_translation_nested_keys():
    """Test translation with nested keys"""
    assert translation.t("buttons.start", "en") == "Start"
    assert translation.t("buttons.start", "ru") == "Старт"
    assert translation.t("buttons.help", "en") == "Help"
    assert translation.t("buttons.help", "ru") == "Помощь"

def test_translation_with_formatting():
    """Test translation with string formatting"""
    assert translation.t("formatted", "en", name="John") == "Hello, John!"
    assert translation.t("formatted", "ru", name="Иван") == "Привет, Иван!"

def test_translation_fallback():
    """Test fallback to English when translation is missing"""
    # Assuming "nonexistent" key doesn't exist in any language
    assert translation.t("nonexistent", "ru") == "nonexistent"

def test_translation_missing_key():
    """Test behavior when key doesn't exist"""
    assert translation.t("nonexistent", "en") == "nonexistent"

def test_translation_missing_language():
    """Test behavior when language doesn't exist"""
    assert translation.t("welcome", "fr") == "Welcome"  # Should fallback to English 