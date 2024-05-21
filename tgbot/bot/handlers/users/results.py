from aiogram import types
from aiogram.dispatcher import FSMContext
from tgbot.bot.keyboards.reply import main_markup, get_olympics_markup, start_olympic_markup, get_result_markup
from tgbot.bot.states.main import AdmissionState, OlympiadState, OlimpicResultsState
from olimpic.models import Olimpic, UserOlimpic
from tgbot.bot.utils import get_user
from tgbot.bot.loader import dp, gettext as _
from django.utils import timezone
from utils.bot import get_model_queryset
from utils.bot import get_object_value, parse_telegram_message
from django.conf import settings
from django.db.models import Q


@dp.message_handler(text=_("📈 Natijalar 📉"), state="*")
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
    await message.answer(_("Natijalar bilan tanishing"), reply_markup=markup)
    await OlimpicResultsState.olimpics.set()


@dp.message_handler(state=OlimpicResultsState.olimpics)
async def get_result(message: types.Message, state: FSMContext):
    if message.text == _("🔙 Orqaga"):
        await message.answer(_("Bosh menu"), reply_markup=main_markup())
        await state.finish()
        return
    queryset = get_model_queryset(Olimpic, message.text)
    if not queryset.exists():
        await message.answer(_("Bunday olimpiada topilmadi"))
        await OlimpicResultsState.olimpics.set()
        return
    olympic = queryset.first()

    result_publish_date_time = timezone.template_localtime(olympic.result_publish)
    now_time = timezone.template_localtime(timezone.now())
    is_end_time = result_publish_date_time > now_time
    markup = await get_result_markup(not is_end_time)

    if is_end_time:
        await message.answer(
            _("Natija {end_time} vaqtda e'lon qilinadi".format(
                end_time=result_publish_date_time.strftime("%d.%m.%Y %H:%M"))),
            reply_markup=markup
        )
        await OlimpicResultsState.olimpic.set()
        return

    results = UserOlimpic.objects.filter(
        olimpic=olympic,
        correct_answers__isnull=False,
        wrong_answers__isnull=False,
        # not_answered__isnull=False,
        olimpic_duration__isnull=False,
    ).order_by("-correct_answers", "wrong_answers", "not_answered", "olimpic_duration").select_related("user")

    if not results:
        await message.answer(
            _("Natijalar topilmadi"),
            reply_markup=markup,
            parse_mode="HTML",
        )
        await OlimpicResultsState.olimpic.set()
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
            not_answered=result.not_answered or '',
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
            not_answered=user_result.not_answered or '',
            olimpic_duration=user_result.olimpic_duration,
        )

    text += _("\nSertificatni Yuklab olish uchun 👇 ni bosing")
    await state.update_data({"olimpic_id": olympic.id})
    await message.answer(text, reply_markup=markup, parse_mode="HTML")
    await OlimpicResultsState.olimpic.set()


@dp.message_handler(state=OlimpicResultsState.olimpic)
async def get_result(message: types.Message, state: FSMContext):
    if message.text == _("🔙 Orqaga"):
        await message.answer(_("Bosh menu"), reply_markup=main_markup())
        await state.finish()
        return

    olimpic_id = await state.get_data()
    user_olimpic = UserOlimpic.objects.filter(user__telegram_id=message.from_user.id,
                                              olimpic_id=olimpic_id['olimpic_id']).first()
    if not user_olimpic:
        await message.answer(_("Siz bu olimpiadada ishtirok etmadingiz"))
        await OlimpicResultsState.olimpic.set()
        return

    if not user_olimpic.certificate:
        await message.answer(_("Sertifikat topilmadi"))
        await OlimpicResultsState.olimpic.set()
        return

    await message.answer_document(user_olimpic.certificate, caption=_("Sertifikat"), reply_markup=main_markup())
    await OlimpicResultsState.olimpic.set()
