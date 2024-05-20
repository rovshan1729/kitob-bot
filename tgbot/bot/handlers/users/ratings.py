from aiogram import types
from aiogram.dispatcher import FSMContext
from tgbot.bot.keyboards.reply import (
    main_markup,
    get_olympics_markup,
    start_olympic_markup,
    get_result_markup,
    get_rating_regions_markup,
    get_rating_district_markup,
    get_rating_school_markup,
    get_rating_classes_markup,
    rating_back

)
from tgbot.bot.states.main import AdmissionState, OlympiadState, OlimpicResultsState, OlimpicRatingState
from olimpic.models import Olimpic, UserOlimpic
from common.models import Region, District, School, Class
from tgbot.bot.utils import get_user
from tgbot.bot.loader import dp, gettext as _
from django.utils import timezone
from utils.bot import get_model_queryset
from utils.bot import get_object_value, parse_telegram_message
from django.conf import settings
from django.db.models import Q


async def olimpi_rating_func(tg_id, olimpic, region, district, school, class_room):
    olympic = Olimpic.objects.get(id=olimpic)
    results = UserOlimpic.objects.filter(
        olimpic=olympic,
        correct_answers__isnull=False,
        wrong_answers__isnull=False,
        not_answered__isnull=False,
        olimpic_duration__isnull=False,
    ).order_by("-correct_answers", "wrong_answers", "not_answered", "olimpic_duration").select_related("user")

    if region is not None:
        results = results.filter(user__region=region)

    if district is not None:
        results = results.filter(user__district=district)

    if school is not None:
        results = results.filter(user__school=school)

    if class_room is not None:
        results = results.filter(user__class_room=class_room)

    if not results:
        return _("Natijalar topilmadi")

    text = _("<b>{}</b> - Natijalari\n\n").format(olympic.title)

    user_result = results.filter(user__telegram_id=tg_id).first()
    query_result = list(results)

    if not user_result:
        text += _("Siz bu olimpiadada ishtirok etmadingiz\n\n")

    for result in results[:10]:
        text += _(
            "{index}) {full_name} - {correct_answers} - {wrong_answers} - {not_answered} - {olimpic_duration}\n"
        ).format(
            index=query_result.index(result) + 1,
            full_name=result.user.full_name,
            correct_answers=result.correct_answers,
            wrong_answers=result.wrong_answers,
            not_answered=result.not_answered,
            olimpic_duration=result.olimpic_duration,
        )

    if user_result and user_result not in results[:10]:
        text += _("---------------------")
        text += _(
            "\n{index}) {full_name} - {correct_answers}/{wrong_answers}/{not_answered} - {olimpic_duration}\n"
        ).format(
            index=query_result.index(user_result) + 1,
            full_name=user_result.user.full_name,
            correct_answers=user_result.correct_answers,
            wrong_answers=user_result.wrong_answers,
            not_answered=user_result.not_answered,
            olimpic_duration=user_result.olimpic_duration,
        )

    return text



@dp.message_handler(text=_("🔝 Reyting 📊"), state="*")
async def get_results(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    tg_user = get_user(message.from_user.id)
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language
    olympics = Olimpic.objects.filter(is_active=True).order_by('start_time', 'end_time')

    if olympics.filter(region__isnull=False).exists():
        olympics = olympics.filter(Q(region=tg_user.region) | Q(region__isnull=True))
    if olympics.filter(district__isnull=False).exists():
        olympics = olympics.filter(Q(district=tg_user.district) | Q(district__isnull=True))
    if olympics.filter(school__isnull=False).exists():
        olympics = olympics.filter(Q(school_id=tg_user.school_id) | Q(school__isnull=True))
    if olympics.filter(class_room__isnull=False).exists():
        olympics = olympics.filter(Q(class_room=tg_user.class_room) | Q(class_room__isnull=True))

    markup = await get_olympics_markup(olympics, language=lang)
    await message.answer(_("Olimpiadalardan birini tanlang"), reply_markup=markup)
    await OlimpicRatingState.olimpic.set()


@dp.message_handler(state=OlimpicRatingState.olimpic)
async def get_resgions(message: types.Message, state: FSMContext):
    if message.text == _("🔙 Orqaga"):
        await message.answer(_("Bosh menyu"), reply_markup=main_markup())
        await state.finish()
        return

    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language

    queryset = get_model_queryset(Olimpic, message.text)
    if not queryset.exists():
        await message.answer(_("Bunday olimpiada topilmadi"))
        await OlimpicRatingState.olimpic.set()
        return

    olympic = queryset.first()
    await state.update_data({
            "olimpic_id": olympic.id,
            'region': None,
            'district': None,
            'school': None,
            'class': None,
        })
    markup = await get_rating_regions_markup(Region.objects.all(), lang)

    await message.answer(_("Viloyatlardan birini tanlang"), reply_markup=markup)
    await OlimpicRatingState.region.set()


@dp.message_handler(state=OlimpicRatingState.region)
async def get_districts(message: types.Message, state: FSMContext):
    if message.text == _("🔙 Orqaga"):
        await state.update_data({"olimpic_id": None})
        tg_user = get_user(message.from_user.id)
        olympics = Olimpic.objects.filter(is_active=True).order_by('start_time', 'end_time')

        if olympics.filter(region__isnull=False).exists():
            olympics = olympics.filter(Q(region=tg_user.region) | Q(region__isnull=True))
        if olympics.filter(district__isnull=False).exists():
            olympics = olympics.filter(Q(district=tg_user.district) | Q(district__isnull=True))
        if olympics.filter(school__isnull=False).exists():
            olympics = olympics.filter(Q(school_id=tg_user.school_id) | Q(school__isnull=True))
        if olympics.filter(class_room__isnull=False).exists():
            olympics = olympics.filter(Q(class_room=tg_user.class_room) | Q(class_room__isnull=True))

        await message.answer(_("Olimpiadalardan birini tanlang"), reply_markup=await get_olympics_markup(olympics))
        await OlimpicRatingState.olimpic.set()
        return

    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language

    region = get_model_queryset(Region, message.text).first()
    if not region and message.text != _("📊 Reytingni ko'rish"):
        await message.answer(_("Bunday viloyat topilmadi"))
        await OlimpicRatingState.region.set()
        return

    if message.text == _("📊 Reytingni ko'rish"):
        text = await olimpi_rating_func(message.from_user.id, data.get("olimpic_id"), None, None, None, None)
        await message.answer(text, reply_markup=await rating_back(), parse_mode="HTML")
        await OlimpicRatingState.rating.set()
        return

    await state.update_data({'region': region.id})

    markup = await get_rating_district_markup(District.objects.filter(parent=region.id), lang)

    await message.answer(_("Tumandagi yoki shahardagi olimpiadalar bilan tanishing"), reply_markup=markup)
    await OlimpicRatingState.district.set()


@dp.message_handler(state=OlimpicRatingState.district)
async def get_schools(message: types.Message, state: FSMContext):
    if message.text == _("🔙 Orqaga"):
        await state.update_data({"region": None})
        await message.answer(_("Viloyatlardan birini tanlang"), reply_markup=await get_rating_regions_markup(Region.objects.all()))
        await OlimpicRatingState.region.set()
        return

    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language

    district = get_model_queryset(District, message.text).first()
    if not district and message.text != _("📊 Reytingni ko'rish"):
        await message.answer(_("Bunday tuman yoki shahar topilmadi"))
        await OlimpicRatingState.district.set()
        return

    if message.text == _("📊 Reytingni ko'rish"):
        text = await olimpi_rating_func(message.from_user.id, data.get("olimpic_id"), data.get("region"), None, None, None)
        await message.answer(text, reply_markup=await rating_back(), parse_mode="HTML")
        await OlimpicRatingState.rating.set()
        return

    await state.update_data({'district': district.id})

    markup = await get_rating_school_markup(School.objects.filter(district=district.id), lang)

    await message.answer(_("Maktabingizni tanlang"), reply_markup=markup)
    await OlimpicRatingState.school.set()


@dp.message_handler(state=OlimpicRatingState.school)
async def get_school_rating(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language

    if message.text == _("🔙 Orqaga"):
        await state.update_data({"district": None})
        await message.answer(_("Tumandagi yoki shahardagi olimpiadalar bilan tanishing"), reply_markup=await get_rating_district_markup(District.objects.filter(parent=data.get("region")), lang))
        await OlimpicRatingState.district.set()
        return


    school = get_model_queryset(School, message.text).first()
    if not school and message.text != _("📊 Reytingni ko'rish"):
        await message.answer(_("Bunday maktab topilmadi"))
        await OlimpicRatingState.school.set()
        return

    if message.text == _("📊 Reytingni ko'rish"):
        text = await olimpi_rating_func(message.from_user.id, data.get("olimpic_id"), data.get("region"), data.get("district"), None,
                                        None)
        await message.answer(text, reply_markup=await rating_back(), parse_mode="HTML")
        await OlimpicRatingState.rating.set()
        return

    await state.update_data({'school': school.id})

    markup = await get_rating_classes_markup()

    await message.answer(_("Sinfingizni tanlang"), reply_markup=markup)
    await OlimpicRatingState.class_room.set()


@dp.message_handler(state=OlimpicRatingState.class_room)
async def get_olimpic_classroom_rating(message: types.Message, state: FSMContext):
    data = await state.get_data()

    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language

    if message.text == _("🔙 Orqaga"):
        await state.update_data({"school": None})
        await message.answer(
            _("Maktabingizni tanlang"),
            reply_markup=await get_rating_school_markup(School.objects.filter(district=data.get("district")), lang))
        await OlimpicRatingState.school.set()
        return


    is_in_class = any(message.text == class_tuple[0] for class_tuple in Class)
    if not is_in_class and message.text != _("📊 Reytingni ko'rish"):
        await message.answer(_("Bunday sinf topilmadi"))
        await OlimpicRatingState.class_room.set()
        return

    if message.text == _("📊 Reytingni ko'rish"):
        text = await olimpi_rating_func(message.from_user.id, data.get("olimpic_id"), data.get("region"),
                                        data.get("district"), data.get("school"),
                                        None)
        await message.answer(text, reply_markup=await rating_back(), parse_mode="HTML")
        await OlimpicRatingState.rating.set()
        return

    await state.update_data({'class': message.text})

    text = await olimpi_rating_func(message.from_user.id, data.get("olimpic_id"), data.get("region"),
                                    data.get("district"), data.get("school"),message.text)
    await message.answer(text, reply_markup=await rating_back(), parse_mode="HTML")
    await OlimpicRatingState.rating.set()
    return


@dp.message_handler(state=OlimpicRatingState.rating)
async def olimpic_rating(message: types.Message, state: FSMContext):
    data = await state.get_data()

    region = data.get("region", None)
    district = data.get("district", None)
    school = data.get("school", None)
    class_room = data.get("class", None)

    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language

    if message.text == _("🔙 Orqaga"):
        await state.update_data({"class": None})
        if not region:
            await message.answer(
                _("Viloyatlardan birini tanlang"),
                reply_markup=await get_rating_regions_markup(Region.objects.all())
            )
            await OlimpicRatingState.region.set()
            return

        elif not district:
            await message.answer(
                _("Tumandagi yoki shahardagi olimpiadalar bilan tanishing"),
                reply_markup=await get_rating_district_markup(District.objects.filter(parent=region), lang))
            await OlimpicRatingState.district.set()
            return

        elif not school:
            await message.answer(
                _("Maktabingizni tanlang"),
                reply_markup=await get_rating_school_markup(School.objects.filter(district=district), lang))
            await OlimpicRatingState.school.set()
            return

        await message.answer(_("Sinfingizni tanlang"), reply_markup=await get_rating_classes_markup())
        await OlimpicRatingState.class_room.set()
        return

    if message.text == _("📊 Reytingni ko'rish"):
        text = await olimpi_rating_func(message.from_user.id, data.get("olimpic_id"), data.get("region"),
                                        data.get("district"), data.get("school"),
                                        None)
        await message.answer(text, reply_markup=await rating_back(), parse_mode="HTML")
        await OlimpicRatingState.rating.set()
        return


    olympic = Olimpic.objects.get(id=data.get("olimpic_id"))
    results = UserOlimpic.objects.filter(
        olimpic=olympic,
        correct_answers__isnull=False,
        wrong_answers__isnull=False,
        not_answered__isnull=False,
        olimpic_duration__isnull=False,
    ).order_by("-correct_answers", "wrong_answers", "not_answered", "olimpic_duration").select_related("user")

    if region is not None:
        results = results.filter(user__region=region)

    if district is not None:
        results = results.filter(user__district=district)

    if school is not None:
        results = results.filter(user__school=school)

    if class_room is not None:
        results = results.filter(user__class_room=class_room)
    if not results:
        await message.answer(
            _("Natijalar topilmadi"),
            reply_markup=await get_result_markup(False),
            parse_mode="HTML",
        )
        await OlimpicRatingState.class_room.set()
        return

    text = _("<b>{}</b> - Natijalari\n\n").format(olympic.title)

    user_result = results.filter(user__telegram_id=message.from_user.id).first()
    query_result = list(results)

    if not user_result:
        text += _("Siz bu olimpiadada ishtirok etmadingiz\n\n")

    for result in results[:10]:
        text += _(
            "{index}) {full_name} - {correct_answers} - {wrong_answers} - {not_answered} - {olimpic_duration}\n"
        ).format(
            index=query_result.index(result) + 1,
            full_name=result.user.full_name,
            correct_answers=result.correct_answers,
            wrong_answers=result.wrong_answers,
            not_answered=result.not_answered,
            olimpic_duration=result.olimpic_duration,
        )

    if user_result and user_result not in results[:10]:
        text += _("---------------------")
        text += _(
            "\n{index}) {full_name} - {correct_answers}/{wrong_answers}/{not_answered} - {olimpic_duration}\n"
        ).format(
            index=query_result.index(user_result) + 1,
            full_name=user_result.user.full_name,
            correct_answers=user_result.correct_answers,
            wrong_answers=user_result.wrong_answers,
            not_answered=user_result.not_answered,
            olimpic_duration=user_result.olimpic_duration,
        )

    await message.answer(text, reply_markup=await rating_back(), parse_mode="HTML")
    # await OlimpicRatingState.rating.set()