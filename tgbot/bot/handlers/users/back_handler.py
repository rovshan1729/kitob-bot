from aiogram import types
from aiogram.dispatcher import FSMContext
from tgbot.bot.keyboards.inline import languages_markup
from tgbot.bot.keyboards.reply import phone_keyboard, main_markup
from tgbot.bot.states.main import AdmissionState
from tgbot.bot.utils import get_user
from django.utils import timezone
from django.db.models import Q
from tgbot.bot.loader import dp, gettext as _


# @dp.message_handler(state=AdmissionState.phone, content_types=types.ContentType.TEXT, text=_("🔙 Orqaga"))
# async def back_to_main(message: types.Message):
#     await message.answer(_("Familiya, Ism va Sharifingizni kiriting"), reply_markup=types.ReplyKeyboardRemove())
#     await AdmissionState.self_introduction.set()


# @dp.message_handler(state=AdmissionState.birth_date, text=_("🔙 Orqaga"))
# async def back_to_phone(message: types.Message):
#     await message.answer(_('Telefon raqamingizni quyidagi tugmani bosgan holda yuboring.'), reply_markup=phone_keyboard)
#     await AdmissionState.phone.set()


# @dp.message_handler(state=AdmissionState.region, text=_("🔙 Orqaga"))
# async def back_to_birth_date(message: types.Message):
#     await message.answer(_("Tug'ilgan kuningizni kiriting.\n"
#                            "Format 15.01.1990"), reply_markup=types.ReplyKeyboardRemove())
#     await AdmissionState.birth_date.set()


# @dp.message_handler(state=AdmissionState.change_language, content_types=types.ContentType.TEXT, text=_("🔙 Orqaga"))
# async def back_to_previous(message: types.Message):
#     await message.answer(_("Tilni o'zgartirishingiz mumkin"), reply_markup=languages_markup)
#     await AdmissionState.change_language.set()
