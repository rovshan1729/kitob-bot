from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.types.chat_member import ChatMemberStatus
from django.conf import settings
from tgbot.bot.loader import bot
from tgbot.models import RequiredGroup, TelegramProfile
from tgbot.bot.loader import gettext as _
from aiogram.dispatcher import FSMContext


from aiogram.utils.callback_data import CallbackData

# Define a CallbackData for handling button presses
skill_cb = CallbackData('skill', 'id', 'level', 'action', 'page',)

ITEMS_PER_PAGE = 5

def get_skills_markup(skills, parent_id=None, page=0, selected_skills=[], language="en"):
    if parent_id is None:
        parent_id = 0 
    
    markup = InlineKeyboardMarkup(row_width=2)
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_skills = skills[start:end]

    for skill in current_skills:
        title = getattr(skill, f"title_{language}")
        markup.add(InlineKeyboardButton(
            text=f"{title} ✅" if skill.id in selected_skills else skill.title, 
            callback_data=skill_cb.new(id=skill.id, level=0, action='select', page=page)
        ))

    if page > 0:
        markup.add(InlineKeyboardButton(
            text="⬅️ Previous", 
            callback_data=skill_cb.new(id=parent_id, level=0, action='paginate', page=page-1)
        ))

    if len(skills) > end:
        markup.add(InlineKeyboardButton(
            text="Next ➡️", 
            callback_data=skill_cb.new(id=parent_id, level=0, action='paginate', page=page+1)
        ))

    if parent_id:
        markup.add(InlineKeyboardButton(
            text="🔙 Back", 
            callback_data=skill_cb.new(id=parent_id, level=1, action='parent', page=0)
        ))

    return markup


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
