import time
import datetime
import json
import uuid
from django.utils import timezone
from telegram import Bot, Poll
from telegram.ext import ConversationHandler
from src.celery_app import app as celery_app
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from django.utils.translation import gettext_lazy
from django.conf import settings
from django.core.cache import cache

from common.models import Settings
from olimpic.models import UserQuestion, UserQuestionOption, UserOlimpic
from bot.models import TelegramBot, TelegramProfile, Notification
from bot.buttons.default import get_main


def _(text):
    return str(gettext_lazy(text))


@celery_app.task
def send_poll(bot_id, telegram_id, user_olimpic_id):
    bot_data = TelegramBot.objects.get(id=bot_id)
    bot = Bot(token=bot_data.bot_token)

    tg_user = TelegramProfile.objects.get(telegram_id=telegram_id, bot=bot_data)
    user_olimpic = UserOlimpic.objects.get(id=user_olimpic_id)

    user_questions = cache.get(f"user_olimpic_{tg_user.id}_{user_olimpic.id}")

    last_question = list(filter(lambda x: x['is_sent'] == True, user_questions))[-1]

    if last_question:
        # TODO: delete last poll
        try:
            if last_question['image'] or last_question['file_content']:
                bot.delete_message(telegram_id, last_question['content_message_id'])
            bot.delete_message(telegram_id, last_question['message_id'])
        except Exception as e:
            print(e)

    user_question = list(filter(lambda x: x['is_sent'] == False, user_questions))

    if not len(user_question):
        user_data = tg_user._user_data
        user_data["olimpic_data"] = None
        user_data["olimpic"] = None
        tg_user.is_olimpic = False
        tg_user.save()
        user_result = list(filter(lambda x: x['is_sent'] == True, user_questions))
        user_olimpic.end_time = timezone.now()

        answered_count = len(user_result)
        correct = len(list(filter(lambda x: x['is_correct'] == True, user_result)))
        wrong = len(list(filter(lambda x: x['is_correct'] == False, user_result)))
        not_answered = len(list(filter(lambda x: x['is_answered'] == False, user_result)))

        user_olimpic.correct_answers = correct
        user_olimpic.wrong_answers = wrong
        user_olimpic.not_answered = not_answered

        olimpic_time = user_olimpic.end_time - user_olimpic.start_time
        user_olimpic.olimpic_duration = str(olimpic_time).split(".")[0]
        user_olimpic.save()


        bot.send_message(
            telegram_id,
            _("🏁 “{olimpic_name}” testi yakunlandi!\n\n"
              "Siz {answered_count} ta savolga javob berdingiz:\n\n"
              "✅ Toʻgʻri – {correct}\n❌ Xato – {wrong}\n"
              "⌛️ Tashlab ketilgan – {not_answered}\n⏱ {time}\n\n"
              "Natija {result_publish} da e'lon qilinadi\n\nNatijalarni ko'rish bo'limida").format(
                olimpic_name=user_olimpic.olimpic.title,
                answered_count=answered_count,
                correct=correct,
                wrong=wrong,
                not_answered=not_answered,
                time=user_olimpic.olimpic_duration,
                result_publish=timezone.template_localtime(user_olimpic.olimpic.result_publish).strftime("%d-%m-%Y %H:%M")
            ),
            reply_markup=get_main()
        )
        return ConversationHandler.END

    user_question = user_question[0]
    question_count = len(user_questions)
    answer_count = len(list(filter(lambda x: x['is_sent'] == True, user_questions)))

    if user_question['image']:
        content_message = bot.send_photo(
            telegram_id,
            user_question['image'],
        )
        user_question['content_message_id'] = content_message.message_id

    if user_question['file_content']:
        content_message = bot.send_document(
            telegram_id,
            user_question['file_content'],
        )
        user_question['content_message_id'] = content_message.message_id

    message = bot.send_poll(
        telegram_id,
        f"[{answer_count + 1}/{question_count}] {user_question[f'text_{tg_user.language}']}",
        options=[option[f'title_{tg_user.language}'] for option in user_question['options']],
        type=Poll.REGULAR,
        open_period=user_question['duration'],
        is_anonymous=False,
        protect_content=True,
    )

    data = {
        'bot_id': tg_user.bot.id,
        'telegram_id': tg_user.telegram_id,
        "user_olimpic_id": user_olimpic.id,
    }

    # schedule, created = IntervalSchedule.objects.get_or_create(
    #     every=user_question['duration'],
    #     period=IntervalSchedule.SECONDS,
    # )
    #
    # next_task = PeriodicTask.objects.create(
    #     interval=schedule,
    #     name=f"{tg_user.telegram_id} {uuid.uuid4()}",
    #     task='apps.bot.tasks.send_poll',
    #     kwargs=json.dumps(data),
    #     one_off=True,
    #     start_time=timezone.now() + datetime.timedelta(seconds=user_question['duration']),
    # )

    next_task = send_poll.apply_async((tg_user.bot_id, tg_user.telegram_id, user_olimpic.id), eta=timezone.now() + datetime.timedelta(seconds=user_question['duration']))

    user_question['is_sent'] = True
    user_question['message_id'] = message.message_id
    user_question['next_task_id'] = next_task.id
    cache.set(f"user_olimpic_{tg_user.id}_{user_olimpic.id}", user_questions, 60 * 60 * 24)



@celery_app.task
def send_notification(notification_id):
    instance = Notification.objects.get(id=notification_id)
    bot = Bot(token=instance.bot.bot_token)

    users_query = TelegramProfile.objects.filter(bot=instance.bot)

    if instance.is_all_users:
        profiles = users_query.all()
    elif instance.is_not_registered:
        profiles = users_query.filter(is_registered=False)
    elif instance.region:
        profiles = users_query.filter(region_id=instance.region_id)
    elif instance.district:
        profiles = users_query.filter(district=instance.district)
    elif instance.school:
        profiles = users_query.filter(school=instance.school)
    elif instance.class_room:
        profiles = users_query.filter(class_room=instance.class_room)
    elif instance.users:
        profiles = instance.users.all()
    else:
        profiles = None


    for profile in profiles:
        time.sleep(0.1)
        if not profile.language:
            profile.language = 'uz'
            profile.save()
        caption = f"<b>{getattr(instance, f'title_{profile.language}')}</b>\n\n{getattr(instance, f'text_{profile.language}')}"
        try:
            if instance.file_content:
                file_content = settings.WEBHOOK_URL + instance.file_content.url
                if instance.file_content.name.split('.')[-1] in ['jpg', 'jpeg', 'png']:
                    bot.send_photo(
                        chat_id=profile.telegram_id,
                        photo=file_content,
                        caption=caption,
                        parse_mode='HTML',
                    )
                    continue
                if instance.file_content.name.split('.')[-1] in ['mp3', 'wav']:
                    bot.send_audio(
                        chat_id=profile.telegram_id,
                        audio=file_content,
                        caption=caption,
                        parse_mode='HTML',
                    )
                    continue
                if instance.file_content.name.split('.')[-1] in ['mp4', 'avi', 'mov']:
                    bot.send_video(
                        chat_id=profile.telegram_id,
                        video=file_content,
                        caption=caption,
                        parse_mode='HTML',
                    )
                    continue
                else:
                    bot.send_document(
                        chat_id=profile.telegram_id,
                        document=file_content,
                        caption=caption,
                        parse_mode='HTML',
                    )
                    continue
            else:
                bot.send_message(
                    chat_id=profile.telegram_id,
                    text=caption,
                    parse_mode='HTML',
                )
                continue
        except Exception as e:
            pass