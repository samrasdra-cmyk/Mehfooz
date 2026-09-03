"""
Alert translation  –  three-tier strategy
=========================================
1. **Google Cloud Translation** (real mode)
   Requires GOOGLE_APPLICATION_CREDENTIALS pointing at a valid service-account
   JSON file.  Best quality; billed per character.

2. **LibreTranslate** (free mode)
   Open-source, no API key needed for the public instance.
   Set LIBRETRANSLATE_URL in .env to point at your own self-hosted instance
   for unlimited, fully private translations.
   Activated automatically when Google Cloud is NOT configured.

3. **Mock passthrough** (demo / offline mode)
   Returns a labelled stub so the full pipeline still runs without any
   external service.  Used when both real services are unavailable.
"""
import logging

import requests

from app.config import GOOGLE_CLOUD_ENABLED, LIBRETRANSLATE_ENABLED, LIBRETRANSLATE_URL, LIBRETRANSLATE_API_KEY

logger = logging.getLogger("mehfooz.translator")

LANGUAGE_NAMES = {"ur": "Urdu", "sd": "Sindhi", "ps": "Pashto"}

# LibreTranslate public instance supports Urdu (ur).
# Sindhi (sd) and Pashto (ps) may not be available on all servers;
# the function falls back gracefully to mock when the API returns an error.
_LIBRETRANSLATE_TIMEOUT = 10  # seconds


def translate_alert(text: str, target_lang: str) -> str:
    """Translate *text* into *target_lang* using the best available backend."""
    if GOOGLE_CLOUD_ENABLED:
        logger.debug("Translator: using Google Cloud")
        return _translate_google(text, target_lang)

    if LIBRETRANSLATE_ENABLED:
        logger.debug("Translator: using LibreTranslate (%s)", LIBRETRANSLATE_URL)
        result = _translate_libre(text, target_lang)
        if result is not None:
            return result
        # LibreTranslate call failed (unsupported language, network error, etc.)
        logger.warning(
            "LibreTranslate failed for lang=%s – falling back to mock", target_lang
        )

    return _translate_mock(text, target_lang)


# ---------------------------------------------------------------------------
# Backend implementations
# ---------------------------------------------------------------------------

def _translate_google(text: str, target_lang: str) -> str:
    """Google Cloud Translation API (tier 1)."""
    from google.cloud import translate_v2 as translate

    client = translate.Client()
    result = client.translate(text, target_language=target_lang)
    return result["translatedText"]


def _translate_libre(text: str, target_lang: str) -> str | None:
    """
    LibreTranslate REST API (tier 2).

    Returns the translated string on success, or *None* on any error so the
    caller can decide whether to fall back to mock mode.
    """
    payload = {
        "q": text,
        "source": "en",
        "target": target_lang,  # "ur", "sd", "ps"
        "format": "text",
    }
    # libretranslate.com requires an API key; self-hosted instances do not.
    if LIBRETRANSLATE_API_KEY:
        payload["api_key"] = LIBRETRANSLATE_API_KEY
    try:
        response = requests.post(
            f"{LIBRETRANSLATE_URL.rstrip('/')}/translate",
            json=payload,
            timeout=_LIBRETRANSLATE_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        translated = data.get("translatedText")
        if translated:
            return translated
        # API returned 200 but no text (e.g. unsupported language pair)
        logger.warning("LibreTranslate returned empty translatedText: %s", data)
        return None
    except requests.exceptions.RequestException as exc:
        logger.error("LibreTranslate request error: %s", exc)
        return None


def _translate_mock(text: str, target_lang: str) -> str:
    """Demo stub – no external service required (tier 3)."""
    lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
    return f"[{lang_name} translation unavailable in demo mode] {text}"
