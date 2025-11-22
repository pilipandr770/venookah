# file: telegram_bot/bot.py

"""
MVP-бот для шефа (поки тільки /start і /ping).
"""

import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

from .config import config

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привіт! Це бот Venookah 2.0 для шефа.\n"
        "Поки що я в демо-режимі. Використай /ping для перевірки."
    )


@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    await message.answer("pong 🟢")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
