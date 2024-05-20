from aiogram import types
from aiogram.dispatcher import FSMContext
from common.models import Region, District, School
from tgbot.bot.keyboards.inline import languages_markup
from tgbot.bot.keyboards.reply import phone_keyboard, get_regions_markup, get_districts_markup, get_schools_markup, \
    main_markup, get_olympics_markup
from tgbot.bot.states.main import AdmissionState, OlympiadState, MainState
from tgbot.bot.utils import get_user
from django.utils import timezone
from olimpic.models import Olimpic
from tgbot.bot.loader import dp, gettext as _


@dp.message_handler(state=AdmissionState.phone, content_types=types.ContentType.TEXT, text=_("🔙 Orqaga"))
async def back_to_main(message: types.Message):
    await message.answer(_("Familiya, Ism va Sharifingizni kiriting"), reply_markup=types.ReplyKeyboardRemove())
    await AdmissionState.self_introduction.set()


@dp.message_handler(state=AdmissionState.birth_date, text=_("🔙 Orqaga"))
async def back_to_phone(message: types.Message):
    await message.answer(_('Telefon raqamingizni quyidagi tugmani bosgan holda yuboring.'), reply_markup=phone_keyboard)
    await AdmissionState.phone.set()


@dp.message_handler(state=AdmissionState.region, text=_("🔙 Orqaga"))
async def back_to_birth_date(message: types.Message):
    await message.answer(_("Tug'ilgan kuningizni kiriting.\n"
                           "Format 15.01.2002"), reply_markup=types.ReplyKeyboardRemove())
    await AdmissionState.birth_date.set()


@dp.message_handler(state=AdmissionState.district, text=_("🔙 Orqaga"))
async def back_to_region(message: types.Message):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language

    regions = Region.objects.all()
    await message.answer(_("Viloyatingizni tanlang"), reply_markup=await get_regions_markup(regions, lang))
    await AdmissionState.region.set()


@dp.message_handler(state=AdmissionState.school, text=_("🔙 Orqaga"))
async def back_to_district(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language

    districts = District.objects.filter(parent=data.get("region_id"))
    await message.answer(_("Tuman yoki shaharni tanlang"), reply_markup=await get_districts_markup(districts, lang))
    await AdmissionState.district.set()


@dp.message_handler(state=AdmissionState.collect_data, text=_("🔙 Orqaga"))
async def back_to_region(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language

    schools = School.objects.filter(
        district=data.get("district_id")
    )
    await message.answer(_("Maktabingizni tanlang"), reply_markup=await get_schools_markup(schools, lang))
    await AdmissionState.school.set()


@dp.message_handler(state=AdmissionState.change_language, content_types=types.ContentType.TEXT, text=_("🔙 Orqaga"))
async def back_to_previous(message: types.Message):
    await message.answer(_("Tilni o'zgartirishingiz mumkin"), reply_markup=languages_markup)
    await AdmissionState.change_language.set()


@dp.message_handler(text=_("🔙 Orqaga"), state=OlympiadState.choose_olympiad)
async def back_main_menu(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language

    await message.answer(_("Main menyudasiz!"), reply_markup=main_markup(lang))
    await MainState.main.set()


@dp.message_handler(text=_("🔙 Orqaga"), state=OlympiadState.confirm_start)
async def back_olympics(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language
    olympics = Olimpic.objects.filter(is_active=True, end_time__gte=timezone.now()).order_by('start_time', 'end_time')
    if olympics.filter(region__isnull=False).exists():
        olympics = olympics.filter(Q(region=tg_user.region) | Q(region__isnull=True))
    if olympics.filter(district__isnull=False).exists():
        olympics = olympics.filter(Q(district=tg_user.district) | Q(district__isnull=True))
    if olympics.filter(school__isnull=False).exists():
        olympics = olympics.filter(Q(school_id=tg_user.school_id) | Q(school__isnull=True))
    if olympics.filter(class_room__isnull=False).exists():
        olympics = olympics.filter(Q(class_room=tg_user.class_room) | Q(class_room__isnull=True))


    markup = await get_olympics_markup(olympics, language=lang)
    await message.answer(_("Olimpiadalar bilan tanishing"), reply_markup=markup)
    await state.set_state(OlympiadState.choose_olympiad)
