# file: telegram_bot/bot.py

"""
MVP-Bot für den Inhaber (derzeit nur /start und /ping).
"""

import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import requests
import io
import os
import atexit

_PIDFILE = os.path.join(os.getenv('TEMP', '.'), 'telegram_bot.pid')

from telegram_bot.config import config

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Lager')],
        [KeyboardButton(text='Shop')],
        [KeyboardButton(text='Seefracht')]
    ], resize_keyboard=True)
    await message.answer(
        "Hallo! Wählen Sie eine Abteilung für die Anfrage:",
        reply_markup=kb
    )


@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    await message.answer("pong 🟢")


@dp.message(lambda message: getattr(message, 'text', None) is not None)
async def handle_text(message: types.Message):
    """Handle plain text messages as owner queries if they come from owner id or any user.

    If message.text matches one of keyboard labels, store department in state (simple) and ask for voice or question.
    Otherwise, treat as query and forward to backend `/api/ai/owner_query`.
    """
    text = (message.text or '').strip()
    if not text:
        await message.answer("Leere Nachricht. Bitte senden Sie einen Text oder eine Sprachnachricht.")
        return
    department_map = {
        'Lager': 'warehouse',
        'Shop': 'shop',
        'Seefracht': 'sea'
    }

    # If user pressed a department button
    if text in department_map:
        await message.answer(f"Sie haben die Abteilung gewählt: {text}. Senden Sie eine Sprachnachricht oder eine Textanfrage, und ich werde das Modell befragen.")
        # store last department in a simple file-based cache per user (for demo)
        tmpdir = os.getenv('TEMP', '.')
        path = os.path.join(tmpdir, f'tg_dept_{message.from_user.id}.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(department_map[text])
        return

    # Otherwise assume it's a query; try to read stored department
    tmpdir = os.getenv('TEMP', '.')
    path = os.path.join(tmpdir, f'tg_dept_{message.from_user.id}.txt')
    dept = None
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                dept = f.read().strip()
        except Exception:
            dept = None

    payload = {'message': text, 'department': dept or 'shop'}
    try:
        resp = requests.post(f"{config.BACKEND_BASE_URL}/api/ai/owner_query", data=payload, timeout=30)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as he:
            # include response body for debugging
            body = he.response.text if getattr(he, 'response', None) is not None else str(he)
            await message.answer(f"Fehler bei der AI-Anfrage: {body[:1000]}")
            return
        j = resp.json()
        reply = j.get('reply') or j.get('error') or 'Keine Antwort'
        await message.answer(reply)
    except requests.exceptions.RequestException as e:
        await message.answer(f"Fehler bei der AI-Anfrage: {str(e)}")
    except Exception as e:
        await message.answer(f"Unerwarteter Fehler: {e}")


@dp.message(lambda message: getattr(message, 'voice', None) is not None or getattr(message, 'audio', None) is not None)
async def handle_voice(message: types.Message):
    # This handler processes voice (voice notes) and audio files.
    if not (message.voice or message.audio):
        return

    # download voice file from Telegram, send to backend as 'audio'
    file_id = message.voice.file_id
    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_bytes = await bot.download_file(file_path)
    except Exception as ex:
        await message.answer(f"Sprachnachricht konnte nicht heruntergeladen werden: {ex}")
        return

    tmpdir = os.getenv('TEMP', '.')
    path = os.path.join(tmpdir, f'tg_dept_{message.from_user.id}.txt')
    dept = None
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                dept = f.read().strip()
        except Exception:
            dept = None

    # `file_bytes` may be bytes or a file-like object; normalize to bytes
    try:
        if hasattr(file_bytes, 'read'):
            data_bytes = file_bytes.read()
        else:
            data_bytes = file_bytes
    except Exception:
        data_bytes = file_bytes

    files = {'audio': ('voice.ogg', io.BytesIO(data_bytes), 'audio/ogg')}
    data = {'department': dept or 'shop'}
    # Debug: include summary of outgoing payload in logs for troubleshooting
    try:
        current = f"POST {config.BACKEND_BASE_URL}/api/ai/owner_query files={list(files.keys())} dept={data.get('department')} size={len(data_bytes) if data_bytes else 0}"
    except Exception:
        current = f"POST {config.BACKEND_BASE_URL}/api/ai/owner_query dept={data.get('department')}"
    try:
        resp = requests.post(f"{config.BACKEND_BASE_URL}/api/ai/owner_query", files=files, data=data, timeout=60)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as he:
            body = he.response.text if getattr(he, 'response', None) is not None else str(he)
            await message.answer(f"Fehler bei der AI-Anfrage: {body[:1000]}")
            return
        j = resp.json()
        await message.answer(j.get('reply') or j.get('error') or 'Keine Antwort')
    except requests.exceptions.RequestException as e:
        await message.answer(f"Fehler bei der AI-Anfrage: {str(e)}")
    except Exception as e:
        await message.answer(f"Unerwarteter Fehler: {e}")


async def main():
    # write PID file so external launchers can detect an already-running bot
    try:
        with open(_PIDFILE, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

    def _cleanup():
        try:
            if os.path.exists(_PIDFILE):
                os.remove(_PIDFILE)
        except Exception:
            pass

    atexit.register(_cleanup)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
