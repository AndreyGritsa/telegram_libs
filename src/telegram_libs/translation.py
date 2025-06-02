import json
import os
from typing import Any


def load_translations() -> dict:
    """Load translations from locales directory

    Returns:
        dict: Translations dictionary
    """
    translations = {}
    # Get the project's root directory (where the script is being run from)
    project_root = os.path.abspath(os.getcwd())
    locales_dir = os.path.join(project_root, 'locales')
    
    if not os.path.exists(locales_dir):
        print(f"Warning: No 'locales' directory found in {project_root}")
        return translations
    
    for filename in os.listdir(locales_dir):
        if filename.endswith('.json'):
            lang = filename.split('.')[0]
            with open(os.path.join(locales_dir, filename), 'r', encoding='utf-8') as f:
                translations[lang] = json.load(f)
    
    return translations

TRANSLATIONS = load_translations()

def t(key: str, lang: str = 'ru', **kwargs: Any) -> str:
    """Get translation for a key with optional formatting"""
    try:
        # Support nested keys like "buttons.start"
        keys = key.split('.')
        value = TRANSLATIONS[lang]
        for k in keys:
            value = value[k]
        
        return value.format(**kwargs) if kwargs else value
    except KeyError:
        # Fallback to English if translation missing
        if lang != 'en':
            return t(key, 'en', **kwargs)
        return key  # Return the key itself as last resort