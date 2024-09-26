from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart, ChatTypeFilter
from aiogram.utils.exceptions import MessageNotModified, MessageToDeleteNotFound
from aiogram.types import ChatType


from tgbot.models import TelegramProfile
from tgbot.bot.keyboards.inline import languages_markup, get_check_button
from tgbot.bot.keyboards.reply import (
    phone_keyboard, 
    back_keyboard,
    main_markup
    )
from tgbot.bot.loader import dp, bot
from tgbot.bot.loader import gettext as _
from tgbot.bot.states.main import AdmissionState
from tgbot.bot.utils import get_user, get_lang

from utils.subscription import get_result



async def do_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = get_user(message.from_user.id)
    language = user.language

    check_subs_message_id = data.get("check_subs_message_id")
    
    if check_subs_message_id:
        try:
            await bot.delete_message(message.from_user.id, check_subs_message_id)
        except MessageToDeleteNotFound:
            print("Delete is not working correctly!")
            
    user = TelegramProfile.objects.filter(telegram_id=message.from_user.id).first()
    
    if not user:
        TelegramProfile.objects.create(
            telegram_id=user.id, 
            username=user.username, 
            language=user.language,
            full_name=user.full_name
        )
    if not user.is_registered:
        
        await message.answer(
            text='Marhamat tilni tanlang! 🇺🇿\nПожалуйста, выберите язык! 🇷🇺',
            reply_markup=languages_markup)
        
        await AdmissionState.language.set()
        
    else:
        await message.answer(_("Bosh menyu."), reply_markup=main_markup(language=language))


@dp.message_handler(CommandStart(), ChatTypeFilter(ChatType.PRIVATE), state="*")
async def bot_start(message: types.Message, state: FSMContext):
    await state.finish()

    final_status, chat_ids = await get_result(user_id=message.from_user.id)
    reply_markup = await get_check_button(chat_ids)

    if not final_status:
        
        if reply_markup:
            content = _(f"Quyidagi kanallarga obuna bo'lishingiz kerak, pastdagi tugmalar ustiga bosing ⬇️\n\n"
                  f"Вам необходимо подписаться на следующие каналы, нажмите на кнопки ниже ⬇️")
            
            check_subs_message = await message.answer(
                text=content,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
            await state.update_data({"check_subs_message_id": check_subs_message.message_id})
            
        else:
            await do_start(message, state)
            
    else:
        await do_start(message, state)


@dp.callback_query_handler(ChatTypeFilter(ChatType.PRIVATE), text="check_subs", )
async def checker(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = get_user(call.message.from_user.id)
    language = user.language

    final_status, chat_ids = await get_result(user_id=call.from_user.id)
    if final_status:
        
        check_subs_message_id = data.get("check_subs_message_id")
        
        if check_subs_message_id:
            try:
                await bot.delete_message(call.from_user.id, check_subs_message_id)
            except MessageToDeleteNotFound:
                await call.message.delete()
                
        user = TelegramProfile.objects.filter(telegram_id=call.from_user.id).first()
        
        if not user:
            TelegramProfile.objects.create(
                telegram_id=user.id,
                username=user.username, 
                language=user.language,
                full_name=user.full_name
            )
            
        if not user.is_registered:
            await call.message.answer(
                text='Marhamat tilni tanlang! 🇺🇿\nПожалуйста, выберите язык! 🇷🇺',
                reply_markup=languages_markup
            )
            await AdmissionState.language.set()
            
        else:
            await call.message.answer(_("Bosh menyu."), reply_markup=main_markup(language=language))
            
    else:
        reply_markup = await get_check_button(chat_ids)
        
        if not reply_markup:
            await call.message.delete()
            await call.answer(_("Barcha kanallarga obuna bo'ldingiz!"))
            
        else:
            try:
                await call.message.edit_reply_markup(reply_markup=reply_markup)
            except MessageNotModified:
                await call.answer(_("Siz obuna bo'lmagan kanallar mavjud!"), show_alert=True)


@dp.message_handler(state=AdmissionState.language)
async def language(message: types.Message, state: FSMContext):
    lang = message.text
    user = get_user(message.from_user.id)
    language = user.language
    
    if not user.is_registered:
        if lang == "O'zbekcha":
            await message.answer("Iltimos, familiyangizni, ismingizni va otangizning ismini kiriting ⬇️",
                                 reply_markup=back_keyboard)   
            await AdmissionState.full_name.set()
            
        elif lang == "Русский":
            await message.answer("️Пожалуйста, напишите, свою фамилию, имя и отчество ⬇️",
                                 reply_markup=back_keyboard)   
            await AdmissionState.full_name.set()
            
        else:
            await message.answer(
                "Iltimos Tugmalardan birini tanlang 🇺🇿\n\n"
                "Пожалуйста, выберите одну из кнопок 🇷🇺", 
                reply_markup=languages_markup
                )       
    else:
        await message.answer(
            text=_("Bosh menyu."),
            reply_markup=main_markup(language=language)
        )
        await state.finish()
        
    user.language = get_lang(lang)
    user.save(update_fields=['language'])


@dp.message_handler(state=AdmissionState.full_name)
async def full_name(message: types.Message, state: FSMContext):
    full_name_text = message.text.strip()
    is_correct = full_name_text.split(' ')

    if 3 >= len(is_correct) > 1 and len(full_name_text) <= 60:
        await state.update_data({"full_name": full_name_text})
        
        await message.answer(
            _('Telefon raqamingizni quyidagi tugmani bosgan holda yuboring.'),
            reply_markup=phone_keyboard
            )
        await AdmissionState.phone_number.set()
        
    elif len(full_name_text) > 60:
        await message.answer(_("Ismingiz 60belgidan uzun bo'lmasligi kerak."))
        
    else:
        await message.answer(_("Faqat Text Formatda Kamida 2ta so'z bilan yozing"))



@dp.message_handler(state=AdmissionState.phone_number, content_types=types.ContentTypes.TEXT)
@dp.message_handler(state=AdmissionState.phone_number, content_types=types.ContentTypes.CONTACT)
async def contact_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    tg_user = get_user(message.from_user.id)
    language = tg_user.language
    
    if message.content_type in types.ContentTypes.TEXT:
        await message.answer(_("Pastdagi tugma orqali raqamingizni yuboring"))
    elif (
        message.content_type in types.ContentTypes.CONTACT and 
        message.contact.phone_number and 
        message.from_user.id == message.contact.user_id
    ):
        phone_number = message.contact.phone_number
        
        # saving data 
        user, created = TelegramProfile.objects.get_or_create(
            telegram_id=message.from_user.id,
            defaults={
                'full_name': data.get("full_name"),
                'phone_number': phone_number,
                'is_registered': True
            }
        )
        if not created:
            user.full_name = data.get("full_name")
            user.phone_number = phone_number
            user.is_registered = True
            user.save()
        
        await message.answer(_("Ro'yxatdan o'tdingiz, ma'lumotlaringiz saqlandi."), reply_markup=main_markup(language=language))
        await state.reset_data()
        await state.finish()

    else:
        await message.answer(_('📲 Iltimos Raqamni Yuborish Tugmasini Bosing'))
        
