from aiogram import types
from aiogram.dispatcher import FSMContext
from tgbot.bot.keyboards.inline import languages_markup
from tgbot.bot.keyboards.reply import main_markup, get_olympics_markup, start_olympic_markup
from tgbot.bot.states.main import AdmissionState, OlympiadState
from olimpic.models import Olimpic, Question, UserOlimpic, UserQuestion, Option
from tgbot.bot.utils import get_user
from tgbot.bot.loader import dp, bot, gettext as _
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

    # if olympics.filter(region__isnull=False).exists():
    #     olympics = olympics.filter(Q(region=tg_user.region) | Q(region__isnull=True))
    # if olympics.filter(district__isnull=False).exists():
    #     olympics = olympics.filter(Q(district=tg_user.district) | Q(district__isnull=True))
    # if olympics.filter(school__isnull=False).exists():
    #     olympics = olympics.filter(Q(school_id=tg_user.school_id) | Q(school__isnull=True))
    # if olympics.filter(class_room__isnull=False).exists():
    #     olympics = olympics.filter(Q(class_room=tg_user.class_room) | Q(class_room__isnull=True))

    markup = await get_olympics_markup(olympics, language=lang)
    await message.answer(_("Olimpiadalar bilan tanishing"), reply_markup=markup)
    await OlympiadState.choose_olympiad.set()


@dp.message_handler(state=OlympiadState.choose_olympiad)
async def choose_olympiad(message: types.Message, state: FSMContext):
    queryset = get_model_queryset(Olimpic, message.text)
    tg_user = get_user(message.from_user.id)
    if queryset.exists():
        olympic = queryset.first()
        if (
                (olympic.region is not None and olympic.region != tg_user.region) or
                (olympic.district is not None and olympic.district != tg_user.district) or
                (olympic.school is not None and olympic.school != tg_user.school) or
                (olympic.class_room is not None and olympic.class_room != tg_user.class_room)
        ):
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


async def send_next_poll(olympic: Olimpic, user_olimpic: UserOlimpic, user: TelegramProfile):
    user_questions = UserQuestion.objects.filter(olimpic=olympic, user_olimpic=user_olimpic, user=user).values_list(
        "question_id", flat=True)
    questions = Question.objects.filter(olimpic=olympic).exclude(id__in=list(user_questions))
    if questions.exists():
        questions = questions.order_by('?')
        question = questions.first()
        option_variants = question.options.all().order_by("?")
        content_message_id = None
        poll_message = await bot.send_poll(chat_id=user.telegram_id,
                                           question=f"[{len(list(user_questions)) + 1} / {olympic.questions.count()}]. {question.text}",
                                           options=[option.title for option in option_variants],
                                           open_period=question.duration, is_anonymous=False,
                                           protect_content=True)
        user_question = UserQuestion.objects.create(olimpic=olympic, user_olimpic=user_olimpic, user=user,
                                                    question=question, is_sent=True,
                                                    poll_id=str(poll_message.poll.id),
                                                    message_id=poll_message.message_id,
                                                    content_message_id=content_message_id if content_message_id else 0)
        user_question.options.set(option_variants)
    else:
        user_questions = UserQuestion.objects.filter(olimpic=olympic, user_olimpic=user_olimpic, user=user)
        answered_count = user_questions.filter(is_answered=True).count()
        correct = user_questions.filter(is_correct=True).count()
        wrong = user_questions.filter(is_answered=True, is_correct=False).count()
        not_answered = user_questions.count() - answered_count
        result_publish = timezone.template_localtime(user_olimpic.olimpic.result_publish).strftime("%d-%m-%Y %H:%M")
        end_time = timezone.now()
        user_olimpic.end_time = end_time
        user_olimpic.correct_answers = correct
        user_olimpic.wrong_answers = wrong
        user.not_answered = not_answered
        olimpic_time = user_olimpic.end_time - user_olimpic.start_time
        user_olimpic.olimpic_duration = str(olimpic_time).split(".")[0]
        user_olimpic.save(
            update_fields=["olimpic_duration", "end_time", "correct_answers", "wrong_answers", "not_answered"])
        await bot.send_message(
            user.telegram_id,
            _("🏁 “{olimpic_name}” testi yakunlandi!\n\n"
              "Siz {answered_count} ta savolga javob berdingiz:\n\n"
              "✅ Toʻgʻri – {correct}\n❌ Xato – {wrong}\n"
              "⌛️ Tashlab ketilgan – {not_answered}\n🕰 {time}\n\n"
              "Natija {result_publish} da e'lon qilinadi\n\nNatijalarni ko'rish bo'limida").format(
                olimpic_name=user_olimpic.olimpic.title,
                answered_count=answered_count,
                correct=correct,
                wrong=wrong,
                not_answered=not_answered,
                time=user_olimpic.olimpic_duration,
                result_publish=result_publish
            ),
            reply_markup=main_markup(language=user.language)
        )


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
                    user = get_user(message.from_user.id)
                    await message.answer(_("Test boshlandi"), reply_markup=types.ReplyKeyboardRemove())
                    start_time = timezone.now()
                    user_olympic = UserOlimpic.objects.create(user=user, olimpic=olympic, start_time=start_time)
                    question = questions.first()
                    option_variants = question.options.all().order_by("?")
                    content_message_id = None
                    if question.image:
                        image = str(settings.BACK_END_URL) + question.image.url
                        try:
                            content = await message.answer_photo(photo=image)
                            content_message_id = content.message_id
                        except Exception as error:
                            print(error)
                    if question.file_content:
                        file = str(settings.BACK_END_URL) + question.file_content.url
                        try:
                            content = await message.answer_document(document=file)
                            content_message_id = content.message_id
                        except Exception as error:
                            print(error)
                    poll_message = await message.answer_poll(
                        question=f"[1 / {olympic.questions.count()}]. {question.text}",
                        options=[option.title for option in option_variants],
                        open_period=question.duration, is_anonymous=False,
                        protect_content=True)
                    # await state.update_data({"current_poll_id": poll_message.poll.id})
                    user_question = UserQuestion.objects.create(olimpic=olympic, user_olimpic=user_olympic, user=user,
                                                                question=question, is_sent=True,
                                                                poll_id=str(poll_message.poll.id),
                                                                message_id=poll_message.message_id,
                                                                content_message_id=content_message_id if content_message_id else 0)
                    user_question.options.set(option_variants)
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
    user = get_user(user_id)
    user_question = UserQuestion.objects.filter(poll_id=str(poll_id), user=user).first()
    if user_question:
        option = user_question.question.options.filter(is_correct=True).first()
        if option and len(option_ids) == 1:
            user_option = option_ids[0]
            correct_option_id = option.id
            user_option_id = list(user_question.options.all().values_list('id', flat=True))[user_option]
            user_question.is_answered = True
            user_question.is_correct = bool(correct_option_id == user_option_id)
            user_question.user_option = Option.objects.filter(id=user_option_id).first()
            user_question.save(update_fields=["is_answered", "is_correct", "user_option"])
            try:
                if user_question.message_id:
                    await bot.delete_message(user_id, user_question.message_id)
                if user_question.question.image or user_question.question.file_content:
                    await bot.delete_message(user_id, user_question.content_message_id)
            except Exception as e:
                print(e)
            # send another poll if olympic questions is not finished
            await send_next_poll(olympic=user_question.olimpic, user_olimpic=user_question.user_olimpic, user=user)
        else:
            await bot.send_message(chat_id=user_id, text=_("Javob berishda xatolik yuzaga keldi"))
    else:
        await bot.send_message(chat_id=user_id, text=_("Poll va savol topilmadi"))


@dp.message_handler(text=_("🏠 Asosiy menyu"), state="*")
async def back_main_menu(message: types.Message, state: FSMContext):
    await message.answer(_("Main menyudasiz!"), reply_markup=main_markup())
