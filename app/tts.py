"""
Voice alert synthesis.

Real mode: Google Cloud Text-to-Speech.
Mock mode: writes a small placeholder file so downstream code (e.g. an
"attach audio to alert record" step) has a real path to work with, without
needing cloud credentials.
"""
import os
from app.config import GOOGLE_CLOUD_ENABLED, DATA_DIR


def synthesize_voice(text: str, language_code: str, output_filename: str) -> str:
    output_path = os.path.join(DATA_DIR, output_filename)
    if GOOGLE_CLOUD_ENABLED:
        return _synthesize_real(text, language_code, output_path)
    return _synthesize_mock(text, language_code, output_path)


def _synthesize_real(text: str, language_code: str, output_path: str) -> str:
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    with open(output_path, "wb") as f:
        f.write(response.audio_content)
    return output_path


def _synthesize_mock(text: str, language_code: str, output_path: str) -> str:
    # Not a real audio file -- just a stand-in so the pipeline has a path
    # to log/serve. Swap in real TTS credentials for actual audio.
    txt_path = output_path.replace(".mp3", ".mock.txt")
    with open(txt_path, "w") as f:
        f.write(f"[MOCK AUDIO placeholder, lang={language_code}]\n{text}")
    return txt_path
