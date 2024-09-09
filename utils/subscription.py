from typing import Union
from aiogram import Bot
from tgbot.models import RequiredGroup
from tgbot.bot.loader import bot


async def check(user_id, channel: Union[int, str]):
    bot = Bot.get_current()
    member = await bot.get_chat_member(user_id=user_id, chat_id=channel)
    return member.is_chat_member()


async def get_result(user_id):
    final_status = True
    chat_ids = []
    CHANNELS = RequiredGroup.objects.all()
    for channel in CHANNELS:
        status = await check(user_id=user_id, channel=channel.chat_id)
        if status:
            final_status &= status
        else:
            final_status &= False
            chat_ids.append(channel.id)
    return final_status, chat_ids
