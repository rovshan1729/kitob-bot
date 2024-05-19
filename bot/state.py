from django.utils.translation import gettext_lazy
from telegram import ReplyKeyboardRemove

from apps.bot.models import RequiredGroup
from apps.bot.buttons import default
from apps.bot.models import TelegramProfile

from utils.send_message import send_telegram_message
from django.core.cache import cache

from datetime import datetime


def _(text):
    return str(gettext_lazy(text))


class State:
    MAIN_MENU = 1

    # REGISTER
    LANGUAGE = 2
    GROUP_LINKS = 3
    FULL_NAME = 4
    PHONE_NUMBER = 5
    BIRTH_DAY = 6
    REGION = 7
    DISTRICT = 8
    SCHOOL = 9
    CLASS_ROOM = 10

    # OTHER
    CUSTOM_HANDLER = 11

    # OLIMPICS
    OLIMPICS = 12
    OLIMPIC = 13
    SOLVE_QUESTION = 14

    # RESULTS
    OLIMPICS_RESULT = 15
    OLIMPIC_RESULT = 16

    # RATING
    OLIMPICS_RATING = 17
    REGION_RATING = 18
    DISTRICT_RATING = 19
    SCHOOL_RATING = 20
    CLASS_ROOM_RATING = 21
    OLIMPIC_RATING_DETAIL = 22
    REGISTRATION = 23


state = State()