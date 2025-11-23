"""
Whisper/STT helper. If `OPENAI_API_KEY` is set, we'll call OpenAI's audio
transcription endpoint. Returns a dict with keys `text` and `language` when
possible, otherwise returns an empty transcription with `language='unknown'.

The previous legacy mock implementation was accidentally left at the bottom
of the file and shadowed the real function. This file contains the real
implementation that calls OpenAI's `/audio/transcriptions` endpoint.
"""

from typing import BinaryIO, Union
import os
import io
import requests
import logging
from pathlib import Path
from dotenv import dotenv_values, load_dotenv


def _detect_language_simple(text: str) -> str:
    """Very small heuristic to detect Russian/Ukrainian/English based on chars."""
    if not text:
        return 'unknown'
    # Ukrainian-specific letters
    uk_chars = set('іїєґІЇЄҐ')
    ru_chars = set('ёыэъЁЫЭЪ')
    latin = any('a' <= ch.lower() <= 'z' for ch in text)
    if any((c in uk_chars) for c in text):
        return 'uk'
    if any((c in ru_chars) for c in text):
        return 'ru'
    if latin:
        return 'en'
    # fallback to 'ru' if Cyrillic present
    if any('\u0400' <= c <= '\u04FF' for c in text):
        return 'ru'
    return 'unknown'


def get_openai_key() -> Union[str, None]:
    """Resolve OPENAI_API_KEY from environment or repo `.env` file.

    Returns the key string if found and ascii-only, otherwise None.
    """
    logger = logging.getLogger(__name__)
    # 1) try environment
    k = os.getenv('OPENAI_API_KEY')
    if isinstance(k, str):
        k = k.strip()
        if k and k.isascii():
            return k

    # 2) try loading .env from repo root
    try:
        repo_root = Path(__file__).resolve().parents[2]
        env_path = repo_root / '.env'
        if env_path.exists():
            vals = dotenv_values(env_path)
            k2 = vals.get('OPENAI_API_KEY')
            if isinstance(k2, str):
                k2 = k2.strip().strip('"').strip("'")
                if k2 and k2.isascii():
                    return k2
    except Exception:
        logger.debug('Failed to read .env for OPENAI_API_KEY', exc_info=True)

    return None


def transcribe_audio(file_obj: BinaryIO) -> Union[str, dict]:
    """
    Accepts a file-like object (Flask FileStorage or bytes-like). Returns either
    a dict: {'text': ..., 'language': 'en'|'ru'|'uk'|...}.
    """
    # Try to read bytes from the provided object
    audio_bytes = None
    try:
        # Flask's FileStorage supports .read()
        audio_bytes = file_obj.read()
    except Exception:
        try:
            # maybe it's already raw bytes
            audio_bytes = bytes(file_obj)
        except Exception:
            audio_bytes = None

    if not audio_bytes:
        return {'text': '', 'language': 'unknown'}

    # Reuse the module-level key resolver (below) to keep behavior consistent
    # between STT and chat calls.
    openai_key = get_openai_key()
    if not openai_key:
        # fallback mock: return text plus guessed language
        logging.getLogger(__name__).warning('OPENAI_API_KEY not found or invalid (non-ASCII). Using mock transcription.')
        text = '[Mock transcription]'
        lang = _detect_language_simple(text)
        return {'text': text, 'language': lang}

    # Call OpenAI audio transcription endpoint
    try:
        url = 'https://api.openai.com/v1/audio/transcriptions'
        headers = {'Authorization': f'Bearer {openai_key}'}
        files = {'file': ('audio.ogg', io.BytesIO(audio_bytes), 'audio/ogg')}
        data = {'model': 'whisper-1'}
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        resp.raise_for_status()
        j = resp.json()
        text = j.get('text', '')
        lang = _detect_language_simple(text)
        return {'text': text, 'language': lang}
    except requests.RequestException:
        # On failure return empty transcription with unknown language
        return {'text': '', 'language': 'unknown'}
