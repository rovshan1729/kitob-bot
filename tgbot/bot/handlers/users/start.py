import re
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.utils.exceptions import MessageNotModified, MessageToDeleteNotFound
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from bot.models import TelegramProfile
from common.models import Region, District, School, Class
from tgbot.bot.keyboards.inline import languages_markup, get_check_button
from tgbot.bot.keyboards.reply import (phone_keyboard, main_markup, get_regions_markup, get_districts_markup,
                                       get_schools_markup, classes, main_menu_markup)
from tgbot.bot.loader import dp, bot
from tgbot.bot.loader import gettext as _
from tgbot.bot.states.main import AdmissionState
from tgbot.bot.utils import get_user, get_lang
from utils.subscription import get_result


async def do_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language
    check_subs_message_id = data.get("check_subs_message_id")
    if check_subs_message_id:
        try:
            await bot.delete_message(message.from_user.id, check_subs_message_id)
        except MessageToDeleteNotFound:
            print("Delete is not working correctly!")
    user = TelegramProfile.objects.filter(telegram_id=message.from_user.id).first()
    if not user:
        TelegramProfile.objects.create(telegram_id=user.id, first_name=user.first_name, last_name=user.last_name,
                                       username=user.username, language=user.language_code,
                                       full_name=user.full_name)
    if not user.is_registered:
        await message.answer_photo(
            photo="https://globaledu-bot.uicgroup.tech/media/notifications/photo_2024-04-30_16.54.13.jpeg",
            caption='🏆 Boshqarma boshlig\'ining "Kelajak yoshlari" deb nomlangan ingliz tili bo\'yicha onlayn Olimpiadasiga Xush kelibsiz!\n\nMarhamat tilni tanlang! 🇺🇿\nПожалуйста, выберите язык! 🇷🇺\nPlease, select a language! 🇺🇸',
            reply_markup=languages_markup)
        await AdmissionState.full_name.set()
    else:
        await message.answer(_("Bosh menyu"), reply_markup=main_markup(lang))


@dp.message_handler(CommandStart(), state="*")
async def bot_start(message: types.Message, state: FSMContext):
    await state.finish()

    final_status, chat_ids = await get_result(user_id=message.from_user.id)

    reply_markup = await get_check_button(chat_ids)

    if not final_status:
        if reply_markup:
            check_subs_message = await message.answer(
                f"Quyidagi kanallarga obuna bo'lishingiz kerak, pastdagi tugmalar ustiga bosing ⬇️",
                reply_markup=reply_markup,
                disable_web_page_preview=True)
            await state.update_data({"check_subs_message_id": check_subs_message.message_id})
        else:
            await do_start(message, state)
    else:
        await do_start(message, state)


@dp.callback_query_handler(text="check_subs")
async def checker(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(call.message.from_user.id)
        if user:
            lang = user.language

    final_status, chat_ids = await get_result(user_id=call.from_user.id)
    if final_status:
        data = await state.get_data()
        check_subs_message_id = data.get("check_subs_message_id")
        if check_subs_message_id:
            try:
                await bot.delete_message(call.from_user.id, check_subs_message_id)
            except MessageToDeleteNotFound:
                await call.message.delete()
        user = TelegramProfile.objects.filter(telegram_id=call.from_user.id).first()
        if not user:
            TelegramProfile.objects.create(telegram_id=user.id, first_name=user.first_name, last_name=user.last_name,
                                           username=user.username, language=user.language_code,
                                           full_name=user.full_name)
        if not user.is_registered:
            await call.message.answer_photo(
                photo="https://globaledu-bot.uicgroup.tech/media/notifications/photo_2024-04-30_16.54.13.jpeg",
                caption='🏆 Boshqarma boshlig\'ining "Kelajak yoshlari" deb nomlangan ingliz tili bo\'yicha onlayn Olimpiadasiga Xush kelibsiz!\n\nMarhamat tilni tanlang! 🇺🇿\nПожалуйста, выберите язык! 🇷🇺\nPlease, select a language! 🇺🇸',
                reply_markup=languages_markup)
            await AdmissionState.full_name.set()
        else:
            await call.message.answer(_("Bosh menyu"), reply_markup=main_markup(lang))
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


@dp.message_handler(state=AdmissionState.change_language)
@dp.message_handler(state=AdmissionState.full_name)
async def language(message: types.Message, state: FSMContext):
    lang = message.text
    user = get_user(message.from_user.id)
    if not user.is_registered:
        if lang == "O'zbekcha":
            await message.answer("Iltimos, familiyangizni, ismingizni va otangizning ismini kiriting ⬇️",
                                 reply_markup=types.ReplyKeyboardRemove())
            await AdmissionState.self_introduction.set()
        elif lang == "Русский":
            await message.answer("️Пожалуйста, напишите, свою фамилию, имя и отчество ⬇️",
                                 reply_markup=types.ReplyKeyboardRemove())
            await AdmissionState.self_introduction.set()
        elif lang == "English":
            await message.answer("Please, enter your surname, name and middle name ⬇️",
                                 reply_markup=types.ReplyKeyboardRemove())
            await AdmissionState.self_introduction.set()
        else:
            await message.answer("Iltimos Tugmalardan birini tanlang 🇺🇿\n\n"
                                 "Пожалуйста, выберите одну из кнопок 🇷🇺\n\n"
                                 "Please, select one of the buttons 🇺🇸", reply_markup=languages_markup)
    else:
        await message.answer(_("Siz qilgan o'zgarishlar saqlandi, iltimos botni /start bosib qayta ishga tushiring"),
                             reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
    user.language = get_lang(lang)
    user.save(update_fields=['language'])
    await state.update_data({"language": user.language})


@dp.message_handler(state=AdmissionState.self_introduction)
async def self_introduction(message: types.Message, state: FSMContext):
    is_correct = message.text.split(' ')
    if message.text and len(is_correct) >= 2:
        await state.update_data({"self_introduction": message.text})
        await message.answer(_('Telefon raqamingizni quyidagi tugmani bosgan holda yuboring.'),
                             reply_markup=phone_keyboard)
        await AdmissionState.phone.set()
    else:
        await message.answer(_("Faqat Text Formatda Kamida 2ta so'z bilan yozing"))


@dp.message_handler(state=AdmissionState.phone, content_types=types.ContentTypes.TEXT)
@dp.message_handler(state=AdmissionState.phone, content_types=types.ContentTypes.CONTACT)
async def contact(message: types.Message, state: FSMContext):
    if message.content_type in types.ContentTypes.TEXT:
        await message.answer(_("Pastdagi tugma orqali raqamingizni yuboring"))
    elif message.content_type in types.ContentTypes.CONTACT and message.contact.phone_number and message.from_user.id == message.contact.user_id:
        await state.update_data({"phone": message.contact.phone_number})
        await message.answer(_("Tug'ilgan kuningizni kiriting.\n"
                               "Format 15.01.1990"), reply_markup=types.ReplyKeyboardRemove())
        await AdmissionState.birth_date.set()
    else:
        await message.answer(_('📲 Iltimos Raqamni Yuborish Tugmasini Bosing'))


@dp.message_handler(state=AdmissionState.birth_date)
async def user_birth_date(message: types.Message, state: FSMContext):
    pattern = r'^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(200[0-9]|201[0-5])$'
    if re.match(pattern, message.text):
        regions = Region.objects.all()
        await state.update_data({"birth_date": message.text})
        data = await state.get_data()
        lang = data.get("language")
        if not lang:
            user = get_user(message.from_user.id)
            if user:
                lang = user.language
        await message.answer(_("Viloyatingizni tanlang"), reply_markup=await get_regions_markup(regions, lang))
        await AdmissionState.region.set()

    else:
        await message.answer(_("Tug'ilgan Sanangizni To'g'ri Formatda Kiriting.Masalan :16.07.2002"))


@dp.message_handler(state=AdmissionState.region)
async def user_region(message: types.Message, state: FSMContext):
    if message.text:
        data = await state.get_data()
        lang = data.get("language")
        if not lang:
            user = get_user(message.from_user.id)
            if user:
                lang = user.language

        region = Region.objects.filter(
            Q(title=message.text) | Q(title_uz=message.text) | Q(title_ru=message.text) | Q(title_en=message.text)
        ).first()
        if region is not None:
            districts = District.objects.filter(
                parent=region.id
            )
            await state.update_data({"region_id": region.id})
            await message.answer(_("Tuman yoki shaharni tanlang"),
                                 reply_markup=await get_districts_markup(districts, lang))
            await AdmissionState.district.set()
        else:
            regions = Region.objects.all()
            await message.answer(_("Viloyatingizni tanlang"), reply_markup=await get_regions_markup(regions, lang))
    else:
        await message.answer(_("Iltimos To'g'ri Formatda Kiriting (16.07.2002)"))


@dp.message_handler(state=AdmissionState.district)
async def user_district(message: types.Message, state: FSMContext):
    if message.text:
        data = await state.get_data()
        lang = data.get("language")
        if not lang:
            user = get_user(message.from_user.id)
            if user:
                lang = user.language

        district = District.objects.filter(
            Q(title=message.text) | Q(title_uz=message.text) | Q(title_ru=message.text) | Q(title_en=message.text)
        ).first()
        if district is not None:
            schools = School.objects.filter(
                district=district.id
            )
            await state.update_data({"district_id": district.id})
            await message.answer(_("Maktabingizni tanlang"), reply_markup=await get_schools_markup(schools, lang))
            await AdmissionState.school.set()
        else:
            data = await state.get_data()
            districts = District.objects.filter(
                parent=data.get("region_id")
            )
            await message.answer(_("Tuman yoki shaharni tanlang"),
                                 reply_markup=await get_districts_markup(districts, lang))

    else:
        await message.answer(_("Iltimos To'g'ri Formatda Kiriting (16.07.2002)"))


@dp.message_handler(state=AdmissionState.school)
async def user_school(message: types.Message, state: FSMContext):
    if message.text:
        school = School.objects.filter(
            Q(title=message.text) | Q(title_uz=message.text) | Q(title_ru=message.text) | Q(title_en=message.text)
        ).first()
        if school is not None:
            await state.update_data({"school_id": school.id})
            await message.answer(_("Sinfingizni Tanlang"),
                                 reply_markup=classes)
            await AdmissionState.collect_data.set()
        else:
            data = await state.get_data()
            lang = data.get("language")
            if not lang:
                user = get_user(message.from_user.id)
                if user:
                    lang = user.language

            data = await state.get_data()
            schools = School.objects.filter(
                district=data.get("district_id")
            )
            await message.answer(_("Maktabingizni tanlang"), reply_markup=await get_schools_markup(schools,lang))
    else:
        await message.answer(_("Iltimos Tugmalardan Birini Tanlang"))


@dp.message_handler(state=AdmissionState.collect_data)
async def collect_user_data(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language
    is_in_class = any(message.text == class_tuple[0] for class_tuple in Class)

    if is_in_class:
        user = TelegramProfile.objects.filter(
            telegram_id=message.from_user.id
        ).first()
        if user:
            user.full_name = data.get("self_introduction")
            user.phone_number = data.get("phone")
            user.birth_day = datetime.strptime(data.get("birth_date"), "%d.%m.%Y").date()
            user.region_id = data.get("region_id")
            user.district_id = data.get("district_id")
            user.school_id = data.get("school_id")
            user.class_room = message.text
            user.is_registered = True
            user.save(
                update_fields=["full_name", "phone_number", "birth_day", "region", "district", "school", "class_room",
                               "is_registered"])
        else:
            TelegramProfile.objects.create(
                telegram_id=message.from_user.id,
                full_name=data.get("self_introduction"),
                phone_number=data.get("phone"),
                birth_day=datetime.strptime(data.get("birth_date"), "%d.%m.%Y").date(),
                region_id=data.get("region_id"),
                district_id=data.get("district_id"),
                school_id=data.get("school_id"),
                class_room=message.text,
                is_registered=True,
            )
        await message.answer(text=_("Ma'lumotlaringiz qabul qilindi"), reply_markup=main_markup(lang))
        await state.finish()
    else:
        await message.answer(_("Iltimos Tugmalardan Birini Tanlang"))
