from aiogram import types
from aiogram.dispatcher import FSMContext
from tgbot.bot.keyboards.inline import languages_markup, get_skills_markup
from tgbot.bot.keyboards.reply import (
    phone_keyboard, 
    main_markup, 
    back_keyboard, 
    select_plan, 
    plan_button
    )

from tgbot.bot.states.main import AdmissionState
from tgbot.bot.utils import get_user
from django.utils import timezone
from django.db.models import Q
from tgbot.bot.loader import dp, gettext as _
from tgbot.models import SelectPlan, Skill
from aiogram.utils.callback_data import CallbackData



@dp.message_handler(state=AdmissionState.full_name, content_types=types.ContentType.TEXT, text=_("🔙 Orqaga"))
async def back_to_language(message: types.Message):
    await message.answer(
                text='Marhamat tilni tanlang! 🇺🇿\nПожалуйста, выберите язык! 🇷🇺\nPlease, select a language! 🇺🇸',
                reply_markup=languages_markup)
    await AdmissionState.language.set()


@dp.message_handler(state=AdmissionState.phone_number, content_types=types.ContentType.TEXT, text=_("🔙 Orqaga"))
async def back_to_full_name(message: types.Message):
    await message.answer(_("Familiya, Ism va Sharifingizni kiriting"), reply_markup=back_keyboard)
    await AdmissionState.full_name.set()


@dp.message_handler(state=AdmissionState.email, text=_("🔙 Orqaga"))
async def back_to_phone(message: types.Message):
    await message.answer(_('Telefon raqamingizni quyidagi tugmani bosgan holda yuboring.'), reply_markup=phone_keyboard)
    await AdmissionState.phone_number.set()
    

@dp.message_handler(state=AdmissionState.skill, text=_("🔙 Orqaga"))
async def back_to_email(message: types.Message):
    await message.answer(_("Email ni yuvoring"), reply_markup=back_keyboard)
    await AdmissionState.email.set()
        