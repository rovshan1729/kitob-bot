from aiogram import types
from tgbot.bot.loader import dp
from tgbot.models import TelegramProfile
from tgbot.bot.utils import get_user
from tgbot.bot.states.main import AdmissionState


@dp.message_handler(commands=["restart"], state="*")
async def unregister_command(message: types.Message):
    user = get_user(message.from_user.id)
    if user.is_registered:
        user.is_registered = False
        user.save()
        await message.answer("Your account is unregistered.")
    else:
        await message.answer("You have not registered yet!")
        