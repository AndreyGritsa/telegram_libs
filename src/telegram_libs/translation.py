import json
import os
from typing import Any


def _load_translations_from_dir(locales_dir: str) -> dict:
    """Helper to load translations from a given directory"""
    translations = {}
    if not os.path.exists(locales_dir):
        print(f"Warning: No 'locales' directory found in {locales_dir}")
        return translations
    for filename in os.listdir(locales_dir):
        if filename.endswith('.json'):
            lang = filename.split('.')[0]
            with open(os.path.join(locales_dir, filename), 'r', encoding='utf-8') as f:
                translations[lang] = json.load(f)
    return translations


def load_translations() -> dict:
    """Load translations from locales directory

    Returns:
        dict: Translations dictionary
    """
    # Get the project's root directory (where the script is being run from)
    project_root = os.path.abspath(os.getcwd())
    locales_dir = os.path.join(project_root, 'locales')
    return _load_translations_from_dir(locales_dir)


def load_common_translations() -> dict:
    """Load translations from locales directory in the project

    Returns:
        dict: Translations dictionary
    """
    locales_dir = os.path.join(os.path.dirname(__file__), 'locales')
    return _load_translations_from_dir(locales_dir)


TRANSLATIONS = load_translations()
COMMON_TRANSLATIONS = load_common_translations()


def t(key: str, lang: str = 'ru', common: bool = False, **kwargs: Any) -> str:
    """Get translation for a key with optional formatting"""
    try:
        # Support nested keys like "buttons.start"
        keys = key.split('.')
        if common:
            value = COMMON_TRANSLATIONS[lang]
        else:
            value = TRANSLATIONS[lang]
        for k in keys:
            value = value[k]
        
        return value.format(**kwargs) if kwargs else value
    except KeyError:
        # Fallback to English if translation missing
        if lang != 'en':
            return t(key, 'en', common=common, **kwargs)
        return key  # Return the key itself as last resort