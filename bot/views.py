import json
import os
from queue import Queue

from django.conf import settings
from django.http import JsonResponse
from django.utils.translation import gettext_lazy
from telegram import Update, Bot, Poll, PollAnswer
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    ConversationHandler,
    PicklePersistence,
    DictPersistence,
    BasePersistence,
    CallbackQueryHandler,
    PollHandler,
    MessageHandler,
    PollAnswerHandler,
    Filters,
)

from apps.bot import telegrambot
from apps.bot.state import state
from apps.common.models import Settings
import pickle
import logging
import sentry_sdk


def _(text):
    return str(gettext_lazy(text))


def setup(token):
    bot = Bot(token=token)
    queue = Queue()
    # create the dispatcher
    if not os.path.exists(os.path.join(settings.BASE_DIR, "media", "state_record")):
        os.makedirs(os.path.join(settings.BASE_DIR, "media", "state_record"))
    state_record_dir = os.path.join(settings.BASE_DIR, "media", "state_record")
    pickle_file_path = os.path.join(state_record_dir, f"{bot.username}.pkl")
    try:
        persistence = PicklePersistence(filename=pickle_file_path, single_file=True)

    except (pickle.UnpicklingError, EOFError, AttributeError, ImportError, IndexError) as e:
        sentry_sdk.capture_exception(e)
        # Load the file manually to debug and preserve the original file
        try:
            with open(pickle_file_path, 'rb') as file:
                file_data = file.read()
            sentry_sdk.capture_message(f"Error loading file for debugging: {file_data}", level="error")
        except Exception as read_error:
            sentry_sdk.capture_exception(read_error)

        # Create a new persistence instance with an empty state
        persistence = PicklePersistence(filename=pickle_file_path, single_file=True, store_user_data=True,
                                        store_bot_data=True, store_chat_data=True, on_flush=False)

    dp = Dispatcher(
        bot,
        queue,
        workers=16,
        use_context=True,
        persistence=persistence,
    )


    states = {
        state.MAIN_MENU: [
            MessageHandler(Filters.text(_("Bosh sahifa")), telegrambot.start),
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text(_("Olimpiadaga kirish")), telegrambot.get_olimpics),
            MessageHandler(Filters.regex("^(" + _("Olimpiada natijalarini ko’rish") + ")$"),
                           telegrambot.get_olimpics_result),
            MessageHandler(Filters.regex("^(" + _("Olimpiada reytingini ko’rish") + ")$"),
                           telegrambot.get_olimpics_rating),
            MessageHandler(Filters.regex("^(" + _("Tilni alishtirish") + ")$"), telegrambot.change_language),
            MessageHandler(Filters.text, telegrambot.custom_handlers),
        ],
        state.CUSTOM_HANDLER: [
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text(_("Bosh sahifa")), telegrambot.start),
            MessageHandler(Filters.text, telegrambot.custom_handler)
        ],

        # OLIMPICS
        state.OLIMPICS: [
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text, telegrambot.get_olimpic)
        ],
        state.OLIMPIC: [
            # CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text, telegrambot.start_olimpic),
        ],

        # REGISTER
        state.LANGUAGE: [
            MessageHandler(Filters.text, telegrambot.set_language),
        ],
        state.FULL_NAME: [
            MessageHandler(Filters.text, telegrambot.set_full_name),
        ],
        state.PHONE_NUMBER: [
            MessageHandler(Filters.contact, telegrambot.set_phone_number),
            MessageHandler(Filters.text, telegrambot.set_phone_number),
        ],
        state.BIRTH_DAY: [
            MessageHandler(Filters.text, telegrambot.set_birth_day),
        ],
        state.REGION: [
            MessageHandler(Filters.text, telegrambot.set_region),
        ],
        state.DISTRICT: [
            MessageHandler(Filters.text, telegrambot.set_district),
        ],
        state.SCHOOL: [
            MessageHandler(Filters.text, telegrambot.set_school)
        ],
        state.CLASS_ROOM: [
            MessageHandler(Filters.text, telegrambot.set_class_room)
        ],
        state.GROUP_LINKS: [
            CallbackQueryHandler(telegrambot.check_sub, pattern="check_sub")
        ],

        # RESULTS
        state.OLIMPICS_RESULT: [
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text, telegrambot.get_olimpic_result)
        ],
        state.OLIMPIC_RESULT: [
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text, telegrambot.get_olimpic_certificate),
        ],

        # RATING
        state.OLIMPICS_RATING: [
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text, telegrambot.get_olimpic_rating)
        ],
        state.REGION_RATING: [
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text, telegrambot.get_region_rating)
        ],
        state.DISTRICT_RATING: [
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text, telegrambot.get_district_rating)
        ],
        state.SCHOOL_RATING: [
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text, telegrambot.get_school_rating)
        ],
        state.CLASS_ROOM_RATING: [
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text, telegrambot.get_class_room_rating)
        ],
        state.OLIMPIC_RATING_DETAIL: [
            CommandHandler("start", telegrambot.start),
            MessageHandler(Filters.text, telegrambot.olimpic_rating)
        ]
    }
    entry_points = [
        MessageHandler(Filters.text(_("Bosh sahifa")), telegrambot.start),
        CommandHandler("start", telegrambot.start),
    ]
    fallbacks = [
        MessageHandler(Filters.text(_("Bosh sahifa")), telegrambot.start),
        CommandHandler("start", telegrambot.start),
    ]
    conversation_handler = ConversationHandler(
        entry_points=entry_points,
        states=states,
        fallbacks=fallbacks,
        persistent=True,
        name=f"{bot.username}_conversation",
    )
    dp.add_handler(conversation_handler)
    dp.add_handler(CommandHandler("yordam", telegrambot.help))
    dp.add_handler(PollAnswerHandler(telegrambot.solve_question))
    dp.add_handler(CallbackQueryHandler(telegrambot.check_sub, pattern="check_sub"))
    return dp


# dp, bot = setup(settings.BOT_TOKEN)

def handle_telegram_webhook(request, bot_token):
    bot = Bot(token=bot_token)
    update = Update.de_json(json.loads(request.body.decode('utf-8')), bot)
    dp = setup(bot_token)
    try:
        if update.message.chat.type == 'private':
            dp.process_update(update)
    except Exception as e:
        if update.poll_answer:
            dp.process_update(update)
        if update.callback_query:
            dp.process_update(update)
    return JsonResponse({'status': 'ok'})
