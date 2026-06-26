LANGUAGES = {
    "en": {"name": "English", "native_name": "English", "iso_639_1": "en"},
    "hi": {"name": "Hindi", "native_name": "हिन्दी", "iso_639_1": "hi"},
    "ta": {"name": "Tamil", "native_name": "தமிழ்", "iso_639_1": "ta"},
    "te": {"name": "Telugu", "native_name": "తెలుగు", "iso_639_1": "te"},
    "bn": {"name": "Bengali", "native_name": "বাংলা", "iso_639_1": "bn"},
    "es": {"name": "Spanish", "native_name": "Español", "iso_639_1": "es"},
    "fr": {"name": "French", "native_name": "Français", "iso_639_1": "fr"},
    "de": {"name": "German", "native_name": "Deutsch", "iso_639_1": "de"},
    "ja": {"name": "Japanese", "native_name": "日本語", "iso_639_1": "ja"},
    "ko": {"name": "Korean", "native_name": "한국어", "iso_639_1": "ko"},
    "zh": {"name": "Chinese", "native_name": "中文", "iso_639_1": "zh"},
    "ar": {"name": "Arabic", "native_name": "العربية", "iso_639_1": "ar"},
    "pt": {"name": "Portuguese", "native_name": "Português", "iso_639_1": "pt"},
    "ru": {"name": "Russian", "native_name": "Русский", "iso_639_1": "ru"},
    "it": {"name": "Italian", "native_name": "Italiano", "iso_639_1": "it"},
    "nl": {"name": "Dutch", "native_name": "Nederlands", "iso_639_1": "nl"},
    "sv": {"name": "Swedish", "native_name": "Svenska", "iso_639_1": "sv"},
    "pl": {"name": "Polish", "native_name": "Polski", "iso_639_1": "pl"},
    "tr": {"name": "Turkish", "native_name": "Türkçe", "iso_639_1": "tr"},
    "vi": {"name": "Vietnamese", "native_name": "Tiếng Việt", "iso_639_1": "vi"},
    "th": {"name": "Thai", "native_name": "ไทย", "iso_639_1": "th"},
    "ms": {"name": "Malay", "native_name": "Bahasa Melayu", "iso_639_1": "ms"},
    "id": {"name": "Indonesian", "native_name": "Bahasa Indonesia", "iso_639_1": "id"},
    "he": {"name": "Hebrew", "native_name": "עברית", "iso_639_1": "he"},
}

LANGUAGE_NAMES = {code: meta["name"] for code, meta in LANGUAGES.items()}

__all__ = ["LANGUAGES", "LANGUAGE_NAMES"]