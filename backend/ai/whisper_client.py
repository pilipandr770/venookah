# file: backend/ai/whisper_client.py

"""
Заглушка для Whisper STT.
"""

from typing import BinaryIO


def transcribe_audio(file_obj: BinaryIO) -> str:
    """
    Приймає файловий об’єкт з аудіо і повертає текст (mock).
    """
    # TODO: інтегрувати OpenAI Audio API
    return "[Mock transcription]"
