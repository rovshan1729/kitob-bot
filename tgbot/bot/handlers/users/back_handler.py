from aiogram import types
from tgbot.bot.keyboards.inline import languages_markup
from tgbot.bot.keyboards.reply import back_keyboard
from tgbot.bot.states.main import AdmissionState
from tgbot.bot.loader import dp, gettext as _



@dp.message_handler(state=AdmissionState.full_name, content_types=types.ContentType.TEXT, text=_("🔙 Orqaga"))
async def back_to_language(message: types.Message):
    await message.answer(
                text='Marhamat tilni tanlang! 🇺🇿\nПожалуйста, выберите язык! 🇷🇺',
                reply_markup=languages_markup)
    await AdmissionState.language.set()


@dp.message_handler(state=AdmissionState.phone_number, content_types=types.ContentType.TEXT, text=_("🔙 Orqaga"))
async def back_to_full_name(message: types.Message):
    await message.answer(_("Familiya, Ism va Sharifingizni kiriting"), reply_markup=back_keyboard)
    await AdmissionState.full_name.set()
