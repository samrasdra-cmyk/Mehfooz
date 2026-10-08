"""
Voice alert synthesis
=============================================
1. **Google Cloud TTS** (real mode)
   Requires GOOGLE_APPLICATION_CREDENTIALS. Best quality, billed per character.

2. **Indic Parler-TTS** (Urdu, Sindhi)
   Open-source model accessed through the public AI4Bharat Hugging Face Space.

3. **Edge TTS** (Urdu fallback, Pashto, English)
   Uses Microsoft neural voices via edge-tts; no API key is needed.
   Install: pip install edge-tts

4. **gTTS** (free, no API key – Google Translate TTS endpoint)
   Fallback for English and Urdu if Edge TTS is unavailable.
   Install: pip install gTTS

5. **Mock passthrough** (offline / demo mode)
   Writes a .txt stub so the rest of the pipeline has a real path to log/serve.
"""
import asyncio
import logging
import os

from app.config import DATA_DIR, GOOGLE_CLOUD_ENABLED, TTS_ENGINE

logger = logging.getLogger("mehfooz.tts")

# ---------------------------------------------------------------------------
# Voice / language mapping
# ---------------------------------------------------------------------------

# Edge TTS voice names per language.
# Full voice list: `edge-tts --list-voices`
EDGE_VOICES: dict[str, str] = {
    "en":    "en-US-AriaNeural",
    "en-us": "en-US-AriaNeural",
    "ur":    "ur-PK-UzmaNeural",      # Urdu (Pakistan) – female neural voice
    "ur-in": "ur-PK-UzmaNeural",      # BCP-47 alias used by the pipeline
    "ur-pk": "ur-PK-UzmaNeural",
    "ps":    "ps-AF-LatifaNeural",    # Pashto (Afghanistan) – female neural voice
    "ps-af": "ps-AF-LatifaNeural",
}

# gTTS language codes (BCP-47 → gTTS lang tag)
GTTS_LANGS: dict[str, str] = {
    "en":    "en",
    "en-us": "en",
    "ur":    "ur",
    "ur-in": "ur",
    "ur-pk": "ur",
}


def _normalize(language_code: str) -> str:
    """Lowercase + strip region suffix for lookup."""
    return language_code.lower().strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def synthesize_voice(text: str, language_code: str, output_filename: str) -> str:
    """
    Synthesize *text* to speech and save as an MP3 (or stub) under DATA_DIR.

    Returns the absolute path to the saved file.
    Priority: Google Cloud → Edge TTS → gTTS → Mock.
    """
    output_path = os.path.join(DATA_DIR, output_filename)
    os.makedirs(DATA_DIR, exist_ok=True)

    # Use the open Indic model for Sindhi. Don't label Urdu fallback audio as
    # Sindhi if the model service is unavailable.
    if _normalize(language_code) in {"sd", "sd-in"}:
        try:
            audio = _synthesize_indic_parler(text, _normalize(language_code))
            with open(output_path, "wb") as f:
                f.write(audio)
            return output_path
        except Exception as exc:
            logger.warning("Indic Parler TTS unavailable for Sindhi: %s", exc)
        return _synthesize_mock(text, language_code, output_path)

    if GOOGLE_CLOUD_ENABLED and TTS_ENGINE != "edge" and TTS_ENGINE != "gtts":
        logger.debug("TTS: using Google Cloud")
        return _synthesize_google(text, language_code, output_path)

    if TTS_ENGINE == "gtts":
        logger.debug("TTS: forced gTTS via TTS_ENGINE env var")
        result = _synthesize_gtts(text, language_code, output_path)
        if result:
            return result

    # Default free path: try Edge TTS first, gTTS second
    logger.debug("TTS: trying Edge TTS")
    result = _synthesize_edge(text, language_code, output_path)
    if result:
        return result

    logger.debug("TTS: Edge TTS failed, trying gTTS")
    result = _synthesize_gtts(text, language_code, output_path)
    if result:
        return result

    logger.warning("TTS: all real engines failed, using mock")
    return _synthesize_mock(text, language_code, output_path)


# ---------------------------------------------------------------------------
# Backend implementations
# ---------------------------------------------------------------------------

def _synthesize_google(text: str, language_code: str, output_path: str) -> str:
    """Google Cloud TTS (tier 1)."""
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    with open(output_path, "wb") as f:
        f.write(response.audio_content)
    return output_path


def _synthesize_edge(text: str, language_code: str, output_path: str) -> str | None:
    """
    Microsoft Edge TTS via the `edge-tts` package (tier 2).

    Completely free – uses the same neural voices as Microsoft Edge browser.
    Returns the output path on success, or None on any error.
    """
    try:
        import edge_tts  # pip install edge-tts
    except ImportError:
        logger.info("edge-tts not installed; skipping Edge TTS tier")
        return None

    voice = EDGE_VOICES.get(_normalize(language_code), "ur-PK-UzmaNeural")
    logger.info("Edge TTS: voice=%s lang=%s", voice, language_code)

    async def _run() -> None:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    try:
        asyncio.run(_run())
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        logger.warning("Edge TTS produced an empty file for lang=%s", language_code)
        return None
    except Exception as exc:
        logger.error("Edge TTS error: %s", exc)
        return None


def _synthesize_gtts(text: str, language_code: str, output_path: str) -> str | None:
    """
    gTTS – Google Translate TTS endpoint (tier 3).

    Free, no API key, but hit-rate limited by Google.
    Returns the output path on success, or None on any error.
    """
    try:
        from gtts import gTTS  # pip install gTTS
    except ImportError:
        logger.info("gTTS not installed; skipping gTTS tier")
        return None

    lang = GTTS_LANGS.get(_normalize(language_code))
    if not lang:
        logger.info("gTTS has no configured voice for lang=%s", language_code)
        return None
    logger.info("gTTS: lang=%s (requested=%s)", lang, language_code)

    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        return None
    except Exception as exc:
        logger.error("gTTS error: %s", exc)
        return None


async def synthesize_audio(text: str, language_code: str) -> tuple[bytes, str]:
    """Generate playable audio bytes for the dashboard speech button."""
    language = _normalize(language_code)
    if language in {"ur", "ur-in", "ur-pk", "sd", "sd-in"}:
        try:
            audio = await asyncio.to_thread(_synthesize_indic_parler, text, language)
            return audio, "audio/mpeg"
        except Exception as exc:
            logger.warning("Indic Parler TTS unavailable for %s: %s", language, exc)
            # Urdu has the local Edge voice as a no-key fallback. For Sindhi,
            # let the frontend try a Sindhi voice installed on the device.
            if language in {"sd", "sd-in"}:
                raise RuntimeError("Open Sindhi TTS demo is currently unavailable") from exc

    voice = EDGE_VOICES.get(language)
    if not voice:
        raise ValueError("Unsupported speech language")

    import edge_tts

    audio_chunks = []
    async for packet in edge_tts.Communicate(text, voice).stream():
        if packet.get("type") == "audio":
            audio_chunks.append(packet["data"])
    audio = b"".join(audio_chunks)
    if not audio:
        raise RuntimeError("Speech provider returned empty audio")
    return audio, "audio/mpeg"


def _synthesize_indic_parler(text: str, language: str) -> bytes:
    """Call the public AI4Bharat Indic Parler-TTS Space and return its MP3."""
    from gradio_client import Client

    language_name = "Sindhi" if language in {"sd", "sd-in"} else "Urdu"
    caption = (
        f"A female speaker reads the text clearly and calmly in {language_name}. "
        "Use a natural speaking pace and very clear audio."
    )
    client = Client("ai4bharat/indic-parler-tts", verbose=False)
    result = client.submit(text, caption, api_name="/generate_finetuned").result(timeout=120)
    candidates = list(result) if isinstance(result, (list, tuple)) else [result]

    for candidate in candidates:
        if isinstance(candidate, bytes):
            return candidate
        if isinstance(candidate, dict):
            candidate = candidate.get("path") or candidate.get("name") or candidate.get("url")
        if isinstance(candidate, str) and os.path.isfile(candidate):
            with open(candidate, "rb") as audio_file:
                return audio_file.read()

    raise RuntimeError("Indic Parler-TTS returned no audio file")


def _synthesize_mock(text: str, language_code: str, output_path: str) -> str:
    """Demo stub – no external service required (tier 4)."""
    txt_path = output_path.replace(".mp3", ".mock.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"[MOCK AUDIO placeholder, lang={language_code}]\n{text}")
    return txt_path
