from django.utils.translation import gettext_lazy, get_language
from django.core.cache import cache
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot

from apps.bot.models import RequiredGroup, TelegramBot


def _(text):
    return str(gettext_lazy(text))

def required_group_btn(bot_id):
    language = get_language().split("-")[0]
    keyboards = []
    tg_bot = TelegramBot.objects.get(id=bot_id)
    bot = Bot(token=tg_bot.bot_token)
    if cache.get(f"bot_channels_{bot.username}", None) is None:
        channels = RequiredGroup.objects.filter(bot=tg_bot)
        cache.set(f"bot_channels_{bot.username}", channels)
    else:
        channels = cache.get(f"bot_channels_{bot.username}")

    for group in channels:
        get_chat = bot.get_chat(chat_id=group.chat_id)
        keyboards.append(
            [
                InlineKeyboardButton(
                    text=getattr(group, f"title_{language}"),
                    url=f"https://t.me/{get_chat.username}",
                )
            ]
        )
    keyboards.append(
        [
            InlineKeyboardButton(
                text=_("Tekshirish"),
                callback_data=f"check_sub",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboards)

