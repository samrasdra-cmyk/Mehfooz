"""
Alert translation.

Real mode: Google Cloud Translation (requires GOOGLE_APPLICATION_CREDENTIALS).
Mock mode: returns a tagged passthrough so the pipeline still demonstrates
the multi-language fan-out without needing cloud credentials.
"""
from app.config import GOOGLE_CLOUD_ENABLED

LANGUAGE_NAMES = {"ur": "Urdu", "sd": "Sindhi", "ps": "Pashto"}


def translate_alert(text: str, target_lang: str) -> str:
    if GOOGLE_CLOUD_ENABLED:
        return _translate_real(text, target_lang)
    return _translate_mock(text, target_lang)


def _translate_real(text: str, target_lang: str) -> str:
    from google.cloud import translate_v2 as translate

    client = translate.Client()
    result = client.translate(text, target_language=target_lang)
    return result["translatedText"]


def _translate_mock(text: str, target_lang: str) -> str:
    lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
    return f"[{lang_name} translation unavailable in demo mode] {text}"
