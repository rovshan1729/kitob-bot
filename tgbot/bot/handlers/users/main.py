import os
from aiogram import types
from aiogram.types import InputFile
from aiogram.dispatcher import FSMContext
from tgbot.bot.keyboards.inline import languages_markup
from tgbot.bot.keyboards.reply import main_markup, get_olympics_markup, start_olympic_markup
from tgbot.bot.states.main import AdmissionState, OlympiadState
from olimpic.models import Olimpic, Question, Option
from tgbot.bot.utils import get_user
from tgbot.bot.loader import dp, gettext as _
from django.utils import timezone
from utils.bot import get_model_queryset
from utils.bot import get_object_value, parse_telegram_message
from django.conf import settings
from django.db.models import Q
from bot.models import TelegramProfile


@dp.message_handler(text=_("🌐 Tilni o'zgartirish"), state="*")
async def change_lang(message: types.Message):
    await message.answer(_("Tilni o'zgartirishingiz mumkin"), reply_markup=languages_markup)
    await AdmissionState.change_language.set()


@dp.message_handler(text=_("🏆 Olimpiadalar 🏆"), state="*")
async def get_olympics(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    tg_user = get_user(message.from_user.id)

    if not lang:
        if tg_user:
            lang = tg_user.language
    olympics = Olimpic.objects.filter(is_active=True, end_time__gte=timezone.now()).order_by('start_time', 'end_time')

    if tg_user:
        olympics = olympics.filter(
            Q(region=tg_user.region),
            Q(district=tg_user.district),
            Q(school_id=tg_user.school_id),
            Q(class_room=tg_user.class_room)
        )

    markup = await get_olympics_markup(olympics, language=lang)
    await message.answer(_("Olimpiadalar bilan tanishing"), reply_markup=markup)
    await OlympiadState.choose_olympiad.set()


@dp.message_handler(state=OlympiadState.choose_olympiad)
async def choose_olympiad(message: types.Message, state: FSMContext):
    queryset = get_model_queryset(Olimpic, message.text)
    tg_user = get_user(message.from_user.id)
    if queryset.exists():
        olympic = queryset.first()
        print(olympic.region != tg_user.region)
        if (
                olympic.region != tg_user.region or
                olympic.district != tg_user.district or
                olympic.school != tg_user.school or
                olympic.class_room != tg_user.class_room
        ):
            print("Olympic not for user")
            await message.answer(_("Iltimos Tugmalardan birini Tanlang!"))
        else:
            await state.update_data({"current_olympic_id": olympic.id})
            data = await state.get_data()
            lang = data.get("language")
            if not lang:
                user = get_user(message.from_user.id)
                if user:
                    lang = user.language
            title = get_object_value(olympic, "title", lang)
            description = parse_telegram_message(get_object_value(olympic, "description", lang))
            if olympic.file_id:
                image = olympic.file_id
            else:
                image = str(settings.BACK_END_URL) + olympic.image.url
            try:
                response = await message.answer_photo(photo=image, caption=f"<b>{title}</b>\n\n{description}",
                                                      parse_mode="HTML", reply_markup=start_olympic_markup)
                if not olympic.file_id:
                    olympic.file_id = response.photo[-1].file_id
                    olympic.save(update_fields=["file_id"])
            except Exception as error:
                print(error)
                await message.answer(text=f"<b>{title}</b>\n\n{description}", parse_mode="HTML",
                                     reply_markup=start_olympic_markup)
            await OlympiadState.confirm_start.set()

    else:
        await message.answer(_("Olimpiada mavjud emas!"))


@dp.message_handler(text=_("▶️ Testni boshlash"), state=OlympiadState.confirm_start)
async def start_test(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_olympic_id = data.get("current_olympic_id")
    if current_olympic_id:
        olympic = Olimpic.objects.filter(id=current_olympic_id).first()
        if olympic:
            if olympic.start_time > timezone.now():
                await message.answer(f"Test boshlanish sanasi: {olympic.start_time}")
            else:
                questions = Question.objects.filter(olimpic=olympic).order_by('?')
                if questions:
                    await message.answer(_("Test boshlandi"), reply_markup=types.ReplyKeyboardRemove())
                    question = questions.first()
                    poll_message = await message.answer_poll(question=question.text, options=[option.title for option in
                                                                                              question.options.all()],
                                                             open_period=question.duration, is_anonymous=False,
                                                             protect_content=True)
                    await state.update_data({"current_poll_id": poll_message.poll.id})
                    await OlympiadState.test.set()
                else:
                    await message.answer(_("Hozircha testlar mavjud emas!"))
        else:
            await message.answer(_("Olimpiada mavjud emas!"))
    else:
        await message.answer(_("Olimpiada mavjud emas!"))


@dp.poll_answer_handler()
async def get_poll_answer(poll_answer: types.PollAnswer):
    user_id = poll_answer.user.id
    poll_id = poll_answer.poll_id
    option_ids = poll_answer.option_ids
    print(user_id, poll_id, option_ids)
    print(poll_answer)


@dp.message_handler(text=_("🏠 Asosiy menyu"), state="*")
async def back_main_menu(message: types.Message, state: FSMContext):
    await message.answer(_("Main menyudasiz!"), reply_markup=main_markup())
