from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import ChatTypeFilter
from aiogram.types import ChatType

from tgbot.models import Group
from tgbot.bot.keyboards.reply import group_markup, main_markup
from tgbot.bot.loader import dp
from tgbot.bot.loader import gettext as _
from tgbot.bot.utils import get_user
from tgbot.bot.states.main import GroupStates


@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), text="👤 Guruhni o'zgartirish", state="*")
@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), text="👤 Изменить группу", state="*")
async def change_group_handler(message: types.Message):
    user = get_user(message.from_user.id)
    lang = user.language

    if lang == "uz":
        content = "Guruhingizni tanlang"
    elif lang == "ru":
        content = "Выберите свою группу"
    else:
        content = "Guruhingizni tanlang"

    await message.answer(text=content, reply_markup=group_markup(lang))
    await GroupStates.group.set()


@dp.message_handler(state=GroupStates.group)
async def group_handler(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    lang = user.language
    group = message.text

    if lang == "uz":
        group_instance = Group.objects.filter(title_uz=group).first()
    elif lang == "ru":
        group_instance = Group.objects.filter(title_ru=group).first()
    else:
        group_instance = Group.objects.filter(title_uz=group).first()

    if group_instance:
        user.group = group_instance
        user.save()

    if lang == "uz":
        content = f'Guruhingiz {group} ga oʻzgartirildi'
    elif lang == "ru":
        content = f'Ваша группа изменена на {group}'
    else:
        content = _("Bosh menyu")

    await message.answer(text=content, reply_markup=main_markup(lang))
    await state.finish()



