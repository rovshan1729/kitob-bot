from aiogram import types
from aiogram.dispatcher.filters.builtin import Command

from tgbot.bot.loader import dp


@dp.message_handler(Command("yordam"), state="*")
async def bot_help(message: types.Message):
    text = "Savollaringiz yoki takliflaringiz bo'lsa, ➡️ @roboteachhelp ⬅️ga murojaat qiling!"
    await message.answer(text)
