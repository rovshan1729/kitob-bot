from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.types.chat_member import ChatMemberStatus
from django.conf import settings
from tgbot.bot.loader import bot
from bot.models import RequiredGroup
from tgbot.bot.loader import gettext as _

languages_markup = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=lang[1]),
        ] for lang in settings.LANGUAGES
    ],
    resize_keyboard=True,
)


async def get_check_button(chat_ids: list = []):
    channels_data = []
    channels = RequiredGroup.objects.all().filter(id__in=chat_ids)
    if channels:
        for channel in channels:
            try:
                chat = await bot.get_chat(channel.chat_id)
                invite_link = await chat.export_invite_link()
                channels_data.append({"title": chat.title, "url": invite_link})
            except Exception as error:
                print(error)
                continue
    if channels_data:
        buttons = [[InlineKeyboardButton(text=channel_chat.get("title", "No title"), url=channel_chat.get("url"))] for channel_chat in channels_data]
        buttons.append([InlineKeyboardButton(text=_("✅ Obunalarni tekshirish"), callback_data="check_subs")])
        check_button = InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
        return check_button
    return None


async def get_required_chats_markup(required_chats, user_id):
    keyboard = []
    for chat in required_chats:
        ch = await bot.get_chat(chat.chat_id)
        member = await bot.get_chat_member(ch.id, user_id)
        if member.status not in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
            ChatMemberStatus.CREATOR
        ]:
            keyboard.append([
                InlineKeyboardButton(text=chat.title, url=ch.invite_link)
            ])
    if not keyboard:
        return None
    keyboard.append([
        InlineKeyboardButton(text=_("Obuna bo'ldim/Qo'shildim"), callback_data="subscribed")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def test_skip_inline():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("➡️ O'tkazib yuborish"), callback_data="skip_test")],
        # [InlineKeyboardButton(text=_("🏁 Yakunlash"), callback_data="finished")]
    ])
