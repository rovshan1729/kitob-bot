import os
from telegram import Bot
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler, PollAnswerHandler, ConversationHandler
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.bot import telegrambot
from apps.bot.state import state
from apps.bot.models import TelegramBot

_ = telegrambot._


class Command(BaseCommand):
    help = 'Bot command'

    def handle(self, *args, **options):
        TelegramBot.objects.get_or_create(
            bot_token=settings.BOT_TOKEN,
        )

        updater = Updater(token=settings.BOT_TOKEN, use_context=True)
        dp = updater.dispatcher


        states = {
            state.MAIN_MENU: [
                MessageHandler(Filters.text(_("Bosh sahifa")), telegrambot.start),
                CommandHandler("start", telegrambot.start),
                MessageHandler(Filters.text(_("Olimpiadaga kirish")), telegrambot.get_olimpics),
                MessageHandler(Filters.regex("^(" + _("Olimpiada natijalarini ko’rish") + ")$"),telegrambot.get_olimpics_result),
                MessageHandler(Filters.regex("^(" + _("Olimpiada reytingini ko’rish") + ")$"),telegrambot.get_olimpics_rating),
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
        )
        dp.add_handler(conversation_handler)
        dp.add_handler(PollAnswerHandler(telegrambot.solve_question))
        dp.add_handler(CallbackQueryHandler(telegrambot.check_sub, pattern="check_sub"))

        print("Bot Polling....")
        print(f"Bot username: @{updater.bot.username}")
        updater.start_polling()
        updater.idle()
