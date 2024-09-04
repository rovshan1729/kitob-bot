import datetime
import json
import logging
import time
import uuid

from django.db.models import Q
from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import activate, get_language, gettext_lazy
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Poll,
                      ReplyKeyboardRemove, Update)
from telegram.ext import CallbackContext, ConversationHandler

from apps.bot import models
from apps.bot.models import TelegramProfile
from apps.bot.buttons import default, inline
from apps.common.models import Class, Region, School, District
from apps.olimpic.models import (Olimpic, UserOlimpic, Question, Option, UserQuestion,
                                 UserQuestionOption)
from core.celery_app import app as celery_app
from utils.decorators import get_member, is_subscribe
from apps.bot.tasks import send_poll

from .state import state, State
from .state import state as state_context

logger = logging.getLogger(__name__)


def _(text):
    return str(gettext_lazy(text))


@get_member
def start(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    if not tg_user.language:
        update.message.reply_photo(
            photo="https://globaledu-bot.uicgroup.tech/media/notifications/photo_2024-04-30_16.54.13.jpeg",
            caption=_("Выберите язык/Tilni tanlash/Choose language"),
            reply_markup=default.language_btn(),
            parse_mode="HTML",
        )
        return state.LANGUAGE

    if not tg_user.full_name:
        update.message.reply_text(
            text=_("Familiya, Ism va Sharifingizni kiriting"),
            reply_markup=default.back(),
            parse_mode="HTML"
        )
        return state.FULL_NAME

    if not tg_user.phone_number:
        update.message.reply_text(
            text=_("Telefon raqamingizni yuboring"),
            reply_markup=default.send_contact(is_back=True),
            parse_mode="HTML",
        )
        return state.PHONE_NUMBER

    if not tg_user.birth_day:
        update.message.reply_text(
            text=_("Tug'ilgan kuningizni kiriting.\nFormat 15.01.1990"),
            reply_markup=default.back(),
            parse_mode="HTML",
        )
        return state.BIRTH_DAY

    if not tg_user.region:
        update.message.reply_text(
            text=_("Viloyatni tanlang"),
            reply_markup=default.region_btn(is_back=True),
            parse_mode="HTML"
        )
        return state.REGION

    if not tg_user.district:
        update.message.reply_text(
            text=_("Tuman yoki shaharni tanlang"),
            reply_markup=default.district_btn(
                region_id=tg_user.region_id,
                is_back=True),
            parse_mode="HTML",
        )
        return state.DISTRICT

    if not tg_user.school:
        update.message.reply_text(
            text=_("Maktabni tanlang "),
            reply_markup=default.school_btn(
                district_id=tg_user.district_id,
                is_back=True
            ),
            parse_mode="HTML",
        )
        return state.SCHOOL

    if not tg_user.class_room:
        update.message.reply_text(
            text=_("Sinf topilmadi, sinfni tanlang"),
            reply_markup=default.class_btn(
                is_back=True
            ),
            parse_mode="HTML"
        )
        return state.CLASS_ROOM

    update.message.reply_text(
        text=_("Bosh menu"),
        reply_markup=default.main_btn(tg_user.bot_id),
        parse_mode="HTML",
    )
    return state.MAIN_MENU


@get_member
def set_language(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    lang_text = update.message.text
    lang = None

    if lang_text == _("O'zbekcha"):
        lang = "uz"

    elif lang_text == _("Русский"):
        lang = "ru"

    elif lang_text == _("English"):
        lang = "en"

    if lang:
        tg_user.language = lang
        tg_user.save()
        activate(lang)

        if tg_user.is_registered:
            update.message.reply_text(
                _("Bosh menu 1"),
                reply_markup=default.main_btn(tg_user.bot_id),
                parse_mode="HTML",
            )
            return state.MAIN_MENU

        update.message.reply_text(
            text=_("Familiya, Ism va Sharifingizni kiriting"),
            reply_markup=default.back(),
            parse_mode="HTML"
        )
        return state.FULL_NAME

    update.message.reply_photo(
        photo="https://globaledu-bot.uicgroup.tech/media/notifications/photo_2024-04-30_16.54.13.jpeg",
        caption=_("Выберите язык/Tilni tanlash/Choose language"),
        reply_markup=default.language_btn(),
        parse_mode="HTML",
    )
    return state.LANGUAGE


@get_member
def check_sub(update: Update, context: CallbackContext, tg_user: models.TelegramProfile) -> None:
    """Check user subscription."""
    user_id = update.effective_user.id
    final_status = True
    language = get_language()

    keyboards = []
    if cache.get(f"bot_channels_{context.bot.username}", None) is None:
        channels = models.RequiredGroup.objects.filter(bot__bot_username=context.bot.username)
        cache.set(f"bot_channels_{context.bot.username}", channels, 60 * 5)
    else:
        channels = cache.get(f"bot_channels_{context.bot.username}")

    for channel in channels:
        status = update.callback_query.message.bot.get_chat_member(channel.chat_id, user_id)["status"] in [
            "member",
            "administrator",
            "creator",
            "owner",
        ]
        final_status *= status
        get_channel = update.callback_query.bot.get_chat(channel.chat_id)
        keyboards.append(
            [
                InlineKeyboardButton(
                    text=getattr(channel, f"title_{language}"),
                    url=f"https://t.me/{get_channel.username}",
                )
            ]
        )
    keyboards.append([InlineKeyboardButton(_("Tekshirish"), callback_data="check_sub")])

    if final_status:
        cache.set(f"user_is_subscribe_{user_id}", True, 60 * 60 * 24 * 7)
        update.message.reply_text(
            text=_("Bosh menu"),
            reply_markup=default.main_btn(tg_user.bot_id),
            parse_mode="HTML",
        )
        return state.MAIN_MENU
    else:
        update.callback_query.answer(text=_("Obuna bo'ling"))
        update.callback_query.message.delete()
        update.callback_query.message.reply_text(
            _("Obuna bo'ling"), reply_markup=InlineKeyboardMarkup(keyboards), parse_mode="HTML"
        )


@get_member
def set_full_name(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    """Set fullname for user."""

    full_name = update.message.text
    invalid_name = False

    if full_name == _("🔙 Orqaga"):
        invalid_name = None

    elif full_name[0] == "/":
        invalid_name = True

    elif not full_name.replace(" ", "").replace("'", "", ).replace("`", "").isalpha():
        invalid_name = True

    if len(full_name.split(" ")) < 2:
        invalid_name = True

    if invalid_name is None:
        update.message.reply_photo(
            photo="https://globaledu-bot.uicgroup.tech/media/notifications/photo_2024-04-30_16.54.13.jpeg",
            caption=_("Выберите язык/Tilni tanlash/Choose language"),
            reply_markup=default.language_btn(),
            parse_mode="HTML",
        )
        return state.LANGUAGE

    if not invalid_name:
        tg_user.full_name = full_name
        tg_user.save()

        update.message.reply_text(
            text=_("Telefon raqamingizni yuboring"),
            reply_markup=default.send_contact(is_back=True),
            parse_mode="HTML",
        )
        return state.PHONE_NUMBER

    update.message.reply_text(
        text=_("Familiya, Ism va Sharifingizni kiriting"),
        reply_markup=default.back(),
        parse_mode="HTML"
    )
    return state.FULL_NAME


@get_member
def set_phone_number(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    """Set phone for user."""
    if update.message.text:
        if update.message.text == _("🔙 Orqaga"):
            update.message.reply_text(
                text=_("Familiya, Ism va Sharifingizni kiriting"),
                reply_markup=default.back(),
                parse_mode="HTML"
            )
            return state.FULL_NAME

    if update.message.contact and update.message.contact.user_id == tg_user.telegram_id:
        tg_user.phone_number = update.message.contact.phone_number
        tg_user.save()
        update.message.reply_text(
            text=_("Tug'ilgan kuningizni kiriting.\nFormat 15.01.1990"),
            reply_markup=default.back(),
            parse_mode="HTML",
        )
        return state.BIRTH_DAY

    update.message.reply_text(
        text=_("Telefon raqamingizni yuboring"),
        reply_markup=default.send_contact(is_back=True),
        parse_mode="HTML",
    )
    return state.PHONE_NUMBER


@get_member
def set_birth_day(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    """Set birthday for user."""
    birth_day = update.message.text

    if birth_day == _("🔙 Orqaga"):
        update.message.reply_text(
            text=_("Telefon raqamingizni yuboring"),
            reply_markup=default.send_contact(is_back=True),
            parse_mode="HTML",
        )
        return state.PHONE_NUMBER

    try:
        birth_day = datetime.datetime.strptime(birth_day, "%d.%m.%Y").date()
        tg_user.birth_day = birth_day
        tg_user.save()
        update.message.reply_text(
            text=_("Viloyatni tanlang"),
            reply_markup=default.region_btn(is_back=True),
            parse_mode="HTML"
        )
        return state.REGION

    except:
        pass

    update.message.reply_text(
        text=_("Tug'ilgan kuningizni kiriting.\nFormat 15.01.1990"),
        reply_markup=default.back(),
        parse_mode="HTML",
    )
    return state.BIRTH_DAY


@get_member
def set_region(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    """Set region for user."""
    text = update.message.text

    if text == _("🔙 Orqaga"):
        update.message.reply_text(
            text=_("Tug'ilgan kuningizni kiriting.\nFormat 15.01.1990"),
            reply_markup=default.back(),
            parse_mode="HTML",
        )
        return state.BIRTH_DAY

    region = Region.objects.filter(parent=None).filter(
        Q(title=text) | Q(title_uz=text) | Q(title_ru=text) | Q(title_en=text)
    ).first()

    if region:
        tg_user.region = region
        tg_user.save()

        update.message.reply_text(
            text=_("Tuman yoki shaharni tanlang"),
            reply_markup=default.district_btn(
                region_id=tg_user.region_id,
                is_back=True),
            parse_mode="HTML",
        )
        return state.DISTRICT

    update.message.reply_text(
        text=_("Vioyat topilmadi, viloyatni tanlang"),
        reply_markup=default.region_btn(is_back=True),
        parse_mode="HTML"
    )
    return state.REGION


@get_member
def set_district(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    """Set language for user."""
    text = update.message.text

    if text == _("🔙 Orqaga"):
        update.message.reply_text(
            text=_("Viloyatni tanlang"),
            reply_markup=default.region_btn(is_back=True),
            parse_mode="HTML"
        )
        return state.REGION

    region = tg_user.region
    district = District.objects.filter(parent_id=region).filter(
        Q(title=text) | Q(title_uz=text) | Q(title_ru=text) | Q(title_en=text)
    ).first()

    if district:
        tg_user.district = district
        tg_user.save()

        update.message.reply_text(
            text=_("Maktabni tanlang 1"),
            reply_markup=default.school_btn(
                district_id=tg_user.district_id,
                is_back=True
            ),
            parse_mode="HTML",
        )
        return state.SCHOOL

    update.message.reply_text(
        text=_("Topilmadi, Tuman yoki shaharni tanlang"),
        reply_markup=default.district_btn(
            region_id=tg_user.region_id,
            is_back=True),
        parse_mode="HTML",
    )
    return state.DISTRICT


@get_member
def set_school(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    """Set language for user."""
    text = update.message.text
    if text == _("🔙 Orqaga"):
        update.message.reply_text(
            text=_("Tuman yoki shaharni tanlang"),
            reply_markup=default.district_btn(
                region_id=tg_user.region_id,
                is_back=True),
            parse_mode="HTML",
        )
        return state.DISTRICT

    district_id = tg_user.district_id
    school = School.objects.filter(district_id=district_id).filter(
        Q(title=text) | Q(title_uz=text) | Q(title_ru=text) | Q(title_en=text)
    ).first()

    if school:
        tg_user.school = school
        tg_user.save()

        update.message.reply_text(
            text=_("Sinfni tanlang"),
            reply_markup=default.class_btn(
                is_back=True
            ),
            parse_mode="HTML",
        )
        return state.CLASS_ROOM

    update.message.reply_text(
        text=_("Topilmadi, Maktabni tanlang "),
        reply_markup=default.school_btn(
            district_id=tg_user.district_id,
            is_back=True
        ),
        parse_mode="HTML",
    )
    return state.SCHOOL


@get_member
def set_class_room(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text

    if text == _("🔙 Orqaga"):
        update.message.reply_text(
            text=_("Maktabni tanlang "),
            reply_markup=default.school_btn(
                district_id=tg_user.district_id,
                is_back=True
            ),
            parse_mode="HTML",
        )
        return state.SCHOOL

    for class_room in Class:
        if text == class_room[1]:
            tg_user.class_room = class_room[0]
            tg_user.is_registered = True
            tg_user.save()

            update.message.reply_text(
                text=_("Bosh menu"),
                reply_markup=default.main_btn(tg_user.bot_id),
                parse_mode="HTML",
            )
            return state.MAIN_MENU

    update.message.reply_text(
        text=_("Sinf topilmadi, sinfni tanlang"),
        reply_markup=default.class_btn(
            is_back=True
        ),
        parse_mode="HTML"
    )
    return state.CLASS_ROOM


@get_member
def change_language(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    """Change language for user."""
    update.message.reply_text(
        _("Tilni tanlash"),
        reply_markup=default.language_btn(),
    )

    return state.LANGUAGE


@get_member
def custom_handlers(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    """Send a message asynchronously when the command /start is issued."""
    text = update.message.text
    if text == '/start':
        update.message.reply_text(
            _("Bosh menu\n"),
            reply_markup=default.main_btn(tg_user.bot_id),
            parse_mode="HTML",
        )
        return state.MAIN_MENU

    if text == '/yordam':
        help(update, context)
        return
    if text == _("Olimpiadaga kirish"):
        update.message.reply_text(
            _("Olimpiadalardan birini tanlang\n"),
            reply_markup=default.olimpics_btn(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS

    if text == _("Olimpiada natijalarini ko’rish"):
        update.message.reply_text(
            _("Olimpiadalardan bitini tanlang"),
            reply_markup=default.get_olimpics_result(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS_RESULT
    if text == _("Olimpiada reytingini ko’rish"):
        update.message.reply_text(
            _("Olimpiadalardan bitini tanlang"),
            reply_markup=default.get_olimpics_result(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS_RATING

    if text == _("Tilni alishtirish"):
        update.message.reply_text(
            _("Tilni tanlash"),
            reply_markup=default.language_btn(),
        )
        return state.LANGUAGE
    try:
        button = (
            models.TelegramButton.objects.filter(parent=None, bot=tg_user.bot)
            .filter(Q(title=text) | Q(title_uz=text) | Q(title_ru=text) | Q(title_en=text))
            .first()
        )

        if not button:
            update.message.reply_text(
                _("Bosh menu\n"),
                reply_markup=default.main_btn(tg_user.bot.id),
                parse_mode="HTML",
            )
            return state.MAIN_MENU

        context.user_data["last_button"] = button.id

        if button.content:
            update.message.reply_photo(
                button.content,
                caption=getattr(button, f"text_{tg_user.language}"),
                reply_markup=default.sub_btn(button.id),
                parse_mode="HTML",
            )
            return state.CUSTOM_HANDLER

        update.message.reply_text(
            getattr(button, f"text_{tg_user.language}"),
            reply_markup=default.sub_btn(button.id),
            parse_mode="HTML",
        )
        return state.CUSTOM_HANDLER
    except models.TelegramButton.DoesNotExist:
        update.message.reply_text(
            _("Bosh menu\n"),
            reply_markup=default.main_btn(tg_user.bot_id),
            parse_mode="HTML",
        )
        return state.MAIN_MENU


@get_member
def custom_handler(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text
    last_button = context.user_data["last_button"]
    if not last_button and text == _("🔙 Orqaga"):
        context.user_data['last_button'] = None
        update.message.reply_text(
            _("Bosh menu\n"),
            reply_markup=default.main_btn(tg_user.bot.id),
            parse_mode="HTML",
        )
        return state.MAIN_MENU

    if last_button and text == _("🔙 Orqaga"):
        try:
            button = models.TelegramButton.objects.get(id=last_button)
            context.user_data["last_button"] = button.parent_id

            if not models.TelegramButton.objects.filter(id=button.parent_id).exists():
                update.message.reply_text(
                    _("Bosh menu\n"),
                    reply_markup=default.main_btn(tg_user.bot.id),
                    parse_mode="HTML",
                )
                return state.MAIN_MENU

            update.message.reply_text(
                button.text,
                reply_markup=default.sub_btn(button.parent_id),
                parse_mode="HTML",
            )
            return state.CUSTOM_HANDLER

        except models.TelegramButton.DoesNotExist:
            update.message.reply_text(
                _("Bunday menu topilmadi!"),
                reply_markup=default.sub_btn(last_button),
                parse_mode="HTML",
            )
            return state.CUSTOM_HANDLER

    try:
        button = models.TelegramButton.objects.filter(parent_id=last_button, bot=tg_user.bot).get(title=text)
        context.user_data["last_button"] = button.id

        if button.content:
            update.message.reply_photo(
                button.content,
                caption=button.text,
                reply_markup=default.sub_btn(button.id),
                parse_mode="HTML",
            )
            return state.CUSTOM_HANDLER

        update.message.reply_text(
            getattr(button, f"text_{tg_user.language}"),
            reply_markup=default.sub_btn(button.id),
            parse_mode="HTML",
        )
        return state.CUSTOM_HANDLER
    except models.TelegramButton.DoesNotExist:
        update.message.reply_text(
            _("Bunday menu topilmadi!"),
            reply_markup=default.sub_btn(last_button),
            parse_mode="HTML",
        )
        return state.CUSTOM_HANDLER


@get_member
@is_subscribe
def get_olimpics(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    """Get olimpics for user."""
    if cache.get(f"olimpics_{tg_user.region_id}_{tg_user.district_id}_{tg_user.school_id}_{tg_user.class_room}",
                 None) is None:
        olimpics = Olimpic.objects.filter(is_active=True)

        if olimpics.filter(region__isnull=False).exists():
            olimpics = olimpics.filter(Q(region=tg_user.region) | Q(region__isnull=True))
        if olimpics.filter(district__isnull=False).exists():
            olimpics = olimpics.filter(Q(district=tg_user.district) | Q(district__isnull=True))
        if olimpics.filter(school__isnull=False).exists():
            olimpics = olimpics.filter(Q(school_id=tg_user.school_id) | Q(school__isnull=True))
        if olimpics.filter(class_room__isnull=False).exists():
            olimpics = olimpics.filter(Q(class_room=tg_user.class_room) | Q(class_room__isnull=True))
        cache.set(f"olimpics_{tg_user.region_id}_{tg_user.district_id}_{tg_user.school_id}_{tg_user.class_room}",
                  olimpics, 60 * 30)
    else:
        olimpics = cache.get(
            f"olimpics_{tg_user.region_id}_{tg_user.district_id}_{tg_user.school_id}_{tg_user.class_room}")

    if not olimpics.exists():
        update.message.reply_text(
            _("Olimpiada topilmadi"),
            reply_markup=default.main_btn(tg_user.bot_id),
            parse_mode="HTML",
        )
        return state.MAIN_MENU

    update.message.reply_text(
        _("Olimpiadalardan birini tanlang\n"),
        reply_markup=default.olimpics_btn(tg_user.id),
        parse_mode="HTML",
    )
    return state.OLIMPICS


@get_member
def get_olimpic(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text
    if text == _("🔙 Orqaga") or text == '/start':
        update.message.reply_text(
            _("Bosh menu\n"),
            reply_markup=default.main_btn(tg_user.bot_id),
            parse_mode="HTML",
        )
        return state.MAIN_MENU

    olimpic = (
        Olimpic.objects.filter(Q(title_uz=text) | Q(title_ru=text) | Q(title_en=text)).filter(is_active=True).first()
    )
    if not olimpic:
        update.message.reply_text(
            _("Olimpiadalardan birini tanlang\n"),
            reply_markup=default.olimpics_btn(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS

    if (
            (olimpic.region is not None and olimpic.region != tg_user.region) or
            (olimpic.district is not None and olimpic.district != tg_user.district) or
            (olimpic.school is not None and olimpic.school != tg_user.school) or
            (olimpic.class_room is not None and olimpic.class_room != tg_user.class_room)
    ):
        update.message.reply_text(
            _("Siz bu olimpiadaga kira olmayiz!"),
            reply_markup=default.olimpics_btn(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS

    context.user_data["olimpic"] = olimpic.id
    content = f"<b>{olimpic.title}</b>\n\n{olimpic.description}"
    if olimpic.image:
        update.message.reply_photo(
            olimpic.image,
            caption=content,
            reply_markup=default.olimpic_btn(),
            parse_mode="HTML",
        )
        return state.OLIMPIC

    update.message.reply_text(
        content,
        reply_markup=default.olimpic_btn(),
        parse_mode="HTML",
    )
    return state.OLIMPIC


@get_member
@is_subscribe
def start_olimpic(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text
    now = timezone.now()
    if text == _("🔙 Orqaga"):
        context.user_data["olimpic"] = None
        update.message.reply_text(
            _("Olimpiadalardan birini tanlang\n"),
            reply_markup=default.olimpics_btn(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS

    if text == _("Bosh sahifa") or text == '/start':
        context.user_data["olimpic"] = None
        update.message.reply_text(
            _("Bosh menu\n"),
            reply_markup=default.main_btn(tg_user.bot_id),
            parse_mode="HTML",
        )
        return state.MAIN_MENU

    if text != _("Testni boshlash"):
        update.message.reply_text(
            _("Olimpiadalardan birini tanlang\n"),
            reply_markup=default.olimpics_btn(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS

    olimpic_id = context.user_data["olimpic"]
    olimpic = Olimpic.objects.get(id=olimpic_id)

    if not olimpic.questions.exists():
        update.message.reply_text(
            _("Olimpiadada savollar topilmadi!"),
            reply_markup=default.olimpic_btn(),
        )
        return state.OLIMPIC

    if olimpic.start_time > now:
        update.message.reply_text(
            _("Olimpiada hali boshlanmagan\nBoshlanish sanasi: {start_time}").format(
                start_time=timezone.template_localtime(olimpic.start_time).strftime("%d.%m.%Y"),
            ),
            reply_markup=default.olimpic_btn(),
            parse_mode="HTML",
        )
        return state.OLIMPIC

    if olimpic.end_time < now:
        update.message.reply_text(
            _("Olimpiada tugagan"),
            reply_markup=default.olimpic_btn(),
            parse_mode="HTML",
        )
        return state.OLIMPIC

    user_olimpic, created = UserOlimpic.objects.get_or_create(
        user=tg_user,
        olimpic=olimpic,
    )
    if not created and user_olimpic.end_time:
        update.message.reply_text(
            _("Siz allaqachon ushbu olimpiadada qatnashgansiz!"),
            reply_markup=default.olimpic_btn(),
            parse_mode="HTML",
        )
        return state.OLIMPIC

    msg = update.message.reply_text(_("Olimpiada boshlanmoqda"), reply_markup=ReplyKeyboardRemove())
    msg.delete()

    # start_message = update.message.reply_text(_("3️⃣ ..."), parse_mode="HTML")
    # time.sleep(0.7)
    # start_message.edit_text(_("2️⃣ Tayyormisiz?"), parse_mode="HTML")
    # time.sleep(0.7)
    # start_message.edit_text(_("1️⃣ Sozlanmoqda"), parse_mode="HTML")
    # time.sleep(0.7)
    # start_message.edit_text(_("Test boshlandi"), parse_mode="HTML")
    # start_message.delete()

    user_olimpic.start_time = timezone.now()
    user_olimpic.save()
    questions = olimpic.questions.all().prefetch_related("options", ).order_by("?")
    user_questions = []
    for question in questions:
        options_data = []

        # Extract options data
        for index, option in enumerate(question.options.all().order_by("?")):
            options_data.append({
                "title": option.title,
                "title_uz": option.title_uz,
                "title_ru": option.title_ru,
                "title_en": option.title_en,
                "option": option.id,
                "order": index,
                "is_correct": option.is_correct,
            })

        # Append question data
        user_questions.append({
            "text": question.text,
            "text_uz": question.text_uz,
            "text_ru": question.text_ru,
            "text_en": question.text_en,
            "image": question.image,
            "file_content": question.file_content,
            "duration": question.duration,
            "olympic": question.olimpic_id,
            "user": tg_user.id,
            "question": question.id,
            "is_sent": False,
            "is_answered": False,
            "is_correct": None,
            "message_id": 0,
            "content_message_id": 0,
            "task_id": None,
            "next_task_id": None,
            "options": options_data
        })

    cache.set(f"user_olimpic_{tg_user.id}_{user_olimpic.id}", user_questions, 60 * 60 * 24)
    bot = context.bot
    telegram_id = tg_user.telegram_id

    user_question = list(filter(lambda x: x['is_sent'] == False, user_questions))[0]
    question_count = len(user_questions)
    answer_count = len(list(filter(lambda x: x['is_sent'] == True, user_questions)))

    options = user_question['options']

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
        options=[option[f"title_{tg_user.language}"] for option in options],
        type=Poll.REGULAR,
        open_period=user_question['duration'],
        is_anonymous=False,
        protect_content=True,
    )
    data = {
        "bot_id": tg_user.bot.id,
        "telegram_id": tg_user.telegram_id,
        "user_olimpic_id": user_olimpic.id,
    }
    next_task = send_poll.apply_async((tg_user.bot_id, tg_user.telegram_id, user_olimpic.id),
                                      eta=timezone.now() + datetime.timedelta(seconds=user_question['duration']))
    user_question['is_sent'] = True
    user_question['next_task_id'] = next_task.id
    user_question['message_id'] = message.message_id
    cache.set(f"user_olimpic_{tg_user.id}_{user_olimpic.id}", user_questions, 60 * 60 * 24)

    cache.set(f"olimpic_data_{tg_user.id}", data, 60 * 60 * 24)
    # context.user_data["olimpic_data"] = {
    #     "bot_id": tg_user.bot.id,
    #     "chat_id": tg_user.telegram_id,
    #     "user_olimpic_id": user_olimpic.id,
    # }
    tg_user.is_olimpic = True
    tg_user.save()
    return


@get_member
def solve_question(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    olimpic_data = cache.get(f"olimpic_data_{tg_user.id}")
    bot = context.bot
    telegram_id = tg_user.telegram_id

    user_olimpic = UserOlimpic.objects.get(id=olimpic_data["user_olimpic_id"])
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

    if last_question['next_task_id']:
        # task = PeriodicTask.objects.get(id=last_question['next_task_id'])
        # task.enabled = False
        # task.save()
        celery_app.control.revoke(last_question['next_task_id'], terminate=True)

    last_question['is_answered'] = True

    user_option = list(filter(lambda x: x['order'] == update.poll_answer.option_ids[0], last_question['options']))[0]
    is_correct = user_option['is_correct']

    last_question['is_correct'] = is_correct

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
                result_publish=timezone.template_localtime(user_olimpic.olimpic.result_publish).strftime(
                    "%d-%m-%Y %H:%M")
            ),
            reply_markup=default.get_main()
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
        options=[option[f"title_{tg_user.language}"] for option in user_question['options']],
        type=Poll.REGULAR,
        open_period=user_question['duration'],
        is_anonymous=False,
        protect_content=True,
    )

    data = {
        "bot_id": tg_user.bot.id,
        "telegram_id": tg_user.telegram_id,
        "user_olimpic_id": user_olimpic.id,
    }
    next_task = send_poll.apply_async((tg_user.bot_id, tg_user.telegram_id, user_olimpic.id),
                                      eta=timezone.now() + datetime.timedelta(seconds=user_question['duration']))
    user_question['is_sent'] = True
    user_question['next_task_id'] = next_task.id
    user_question['message_id'] = message.message_id
    cache.set(f"user_olimpic_{tg_user.id}_{user_olimpic.id}", user_questions, 60 * 60 * 24)

    cache.set(f"olimpic_data_{tg_user.id}", data, 60 * 60 * 24)
    return ConversationHandler.END


@get_member
def get_olimpics_result(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    update.message.reply_text(
        _("Olimpiadalardan bitini tanlang"),
        reply_markup=default.get_olimpics_result(tg_user.id),
        parse_mode="HTML",
    )
    print("1", state.OLIMPICS_RESULT)
    return state.OLIMPICS_RESULT


@get_member
def get_olimpic_result(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text
    if text == _("🔙 Orqaga"):
        update.message.reply_text(
            _("Bosh menu\n"),
            reply_markup=default.main_btn(tg_user.bot_id),
            parse_mode="HTML",
        )
        return state.MAIN_MENU

    olimpic = Olimpic.objects.filter(Q(title_uz=text) | Q(title_ru=text) | Q(title_en=text)).first()

    if not olimpic:
        update.message.reply_text(
            _("Olimpiadalardan birini tanlang\n"),
            reply_markup=default.get_olimpics_result(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS_RESULT

    context.user_data["olimpic"] = olimpic.id

    if olimpic.result_publish and olimpic.result_publish > timezone.now():
        update.message.reply_text(
            _("Natija {} vaqtda e'lon qilinadi".format(
                timezone.template_localtime(olimpic.result_publish).strftime("%d-%m-%Y %H:%M"))),
            reply_markup=default.back(),
            parse_mode="HTML",
        )
        return state.OLIMPICS_RESULT

    # if cache.get(f"olimpic_result_{olimpic.id}", None) is None:
    results = UserOlimpic.objects.filter(
        olimpic=olimpic,
        correct_answers__isnull=False,
        wrong_answers__isnull=False,
        not_answered__isnull=False,
        olimpic_duration__isnull=False,
    ).order_by("-correct_answers", "wrong_answers", "not_answered", "olimpic_duration"
               ).select_related("user")
    #     cache.set(f"olimpic_result_{olimpic.id}", results, 60 * 10)
    # else:
    #     results = cache.get(f"olimpic_result_{olimpic.id}")

    if not results:
        update.message.reply_text(
            _("Natijalar topilmadi"),
            reply_markup=default.get_olimpics_result(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS_RESULT

    text = _("<b>{}</b> - Natijalari\n\n").format(olimpic.title)

    user_result = results.filter(user=tg_user).first()
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

    text += _("\nSertificatni Yuklab olish uchun 👇 ni bosing")
    update.message.reply_text(
        text,
        reply_markup=default.get_certificate(),
        parse_mode="HTML",
    )
    return state.OLIMPIC_RESULT


@get_member
def get_olimpic_certificate(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text

    if text == _("🔙 Orqaga"):
        update.message.reply_text(
            _("Olimpiadalardan birini tanlang"),
            reply_markup=default.get_olimpics_result(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS_RESULT

    if text != _("Sertifikatni yuklab olish"):
        update.message.reply_text(
            _("Sertificatni yuklab olish uchun 👇 ni bosing"),
            reply_markup=default.get_certificate(),
            parse_mode="HTML",
        )
        return state.OLIMPIC_RESULT

    user_result = UserOlimpic.objects.filter(user=tg_user, olimpic_id=context.user_data["olimpic"]).first()

    if not user_result:
        update.message.reply_text(
            _("Siz bu olimpiadada ishtirok etmadingiz\n\n"),
            reply_markup=default.back(),
            parse_mode="HTML",
        )
        return state.OLIMPIC_RESULT

    if not user_result.certificate:
        update.message.reply_text(
            _("Sertificat topilmadi\n\n"),
            reply_markup=default.back(),
            parse_mode="HTML",
        )
        return state.OLIMPIC_RESULT

    update.message.reply_document(
        user_result.certificate,
        caption=_("Sertificat"),
        reply_markup=default.back(),
        parse_mode="HTML",
    )
    return state.OLIMPIC_RESULT


@get_member
def get_olimpics_rating(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    update.message.reply_text(
        _("Olimpiadalardan bitini tanlang"),
        reply_markup=default.get_olimpics_result(tg_user.id),
        parse_mode="HTML",
    )
    return state.OLIMPICS_RATING


@get_member
def get_olimpic_rating(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text

    if text == _("🔙 Orqaga"):
        update.message.reply_text(
            _("Bosh menu\n"),
            reply_markup=default.main_btn(tg_user.bot.id),
            parse_mode="HTML",
        )
        return state.MAIN_MENU

    olimpic = Olimpic.objects.filter(Q(title_uz=text) | Q(title_ru=text) | Q(title_en=text)).first()

    if not olimpic:
        update.message.reply_text(
            _("Olimpiadalardan birini tanlang\n"),
            reply_markup=default.get_olimpics_result(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS_RATING

    context.user_data["rating_olimpic"] = olimpic.id
    update.message.reply_text(
        _("Viloyatlardan birini tanlang"),
        reply_markup=default.region_btn(),
        parse_mode="HTML",
    )
    return state.REGION_RATING


@get_member
def get_region_rating(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text
    if text == _("🔙 Orqaga"):
        update.message.reply_text(
            _("Olimpiadalardan birini tanlang\n"),
            reply_markup=default.get_olimpics_result(tg_user.id),
            parse_mode="HTML",
        )
        return state.OLIMPICS_RATING

    region = Region.objects.filter(Q(title_uz=text) | Q(title_ru=text) | Q(title_en=text)).first()
    if not region:
        update.message.reply_text(
            _("Viloyatlardan birini tanlang"),
            reply_markup=default.region_btn(),
            parse_mode="HTML",
        )
        return state.REGION_RATING

    context.user_data["rating_region"] = region.id
    context.user_data["rating_district"] = None
    context.user_data["rating_school"] = None
    context.user_data["rating_class"] = None
    update.message.reply_text(
        _("Tuman yoki shahar"),
        reply_markup=default.district_rating(region.id),
        parse_mode="HTML",
    )
    return state.DISTRICT_RATING


@get_member
def get_district_rating(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text
    if text == _("🔙 Orqaga"):
        context.user_data["rating_region"] = None
        update.message.reply_text(
            _("Viloyatlardan birini tanlang"),
            reply_markup=default.region_btn(),
            parse_mode="HTML",
        )
        return state.REGION_RATING

    if text == _("Reytingni ko'rish"):
        olimpic_rating(update, context)
        return state.OLIMPIC_RATING_DETAIL

    region_id = context.user_data["rating_region"]
    district = District.objects.filter(parent_id=region_id) \
        .filter(Q(title=text) | Q(title_uz=text) | Q(title_ru=text) | Q(title_en=text)) \
        .first()
    if not district:
        update.message.reply_text(
            _("Tuman yoki shahar"),
            reply_markup=default.district_rating(region_id),
            parse_mode="HTML",
        )
        return state.DISTRICT_RATING

    context.user_data["rating_district"] = district.id

    update.message.reply_text(
        _("Maktabni tanlang"),
        reply_markup=default.school_rating(district.id),
        parse_mode="HTML",
    )
    return state.SCHOOL_RATING


@get_member
def get_school_rating(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text
    if text == _("🔙 Orqaga"):
        context.user_data["rating_district"] = None
        update.message.reply_text(
            _("Tuman yoki shahar"),
            reply_markup=default.district_rating(context.user_data["rating_region"]),
            parse_mode="HTML",
        )
        return state.DISTRICT_RATING

    if text == _("Reytingni ko'rish"):
        olimpic_rating(update, context)
        return state.OLIMPIC_RATING_DETAIL

    district_id = context.user_data["rating_district"]
    school = (
        School.objects.filter(district_id=district_id)
        .filter(Q(title_uz=text) | Q(title_ru=text) | Q(title_en=text))
        .first()
    )

    if not school:
        update.message.reply_text(
            _("Maktabni tanlang"),
            reply_markup=default.school_rating(district_id),
            parse_mode="HTML",
        )
        return state.SCHOOL_RATING

    context.user_data["rating_school"] = school.id
    update.message.reply_text(
        _("Sinfni tanlang"),
        reply_markup=default.class_room_rating(school.id),
        parse_mode="HTML",
    )
    return state.CLASS_ROOM_RATING


@get_member
def get_class_room_rating(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text
    if text == _("🔙 Orqaga"):
        context.user_data["rating_school"] = None
        update.message.reply_text(
            _("Maktabni tanlang"),
            reply_markup=default.school_rating(context.user_data["rating_district"]),
            parse_mode="HTML",
        )
        return state.SCHOOL_RATING

    if text == _("Reytingni ko'rish"):
        olimpic_rating(update, context)
        return state.OLIMPIC_RATING_DETAIL

    school_id = context.user_data["rating_school"]
    classes_room = [
        _("5-sinf"),
        _("6-sinf"),
        _("7-sinf"),
        _("8-sinf"),
        _("9-sinf"),
        _("10-sinf"),
        _("11-sinf"),
    ]

    if text not in classes_room:
        update.message.reply_text(
            _("Sinfni tanlang"),
            reply_markup=default.class_room_rating(school_id),
            parse_mode="HTML",
        )
        return state.CLASS_ROOM_RATING

    for class_room in Class:
        if class_room[1] == text:
            class_room = class_room[0]

    context.user_data["rating_class"] = class_room[0]
    olimpic_rating(update, context)
    return state.OLIMPIC_RATING_DETAIL


@get_member
def olimpic_rating(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    text = update.message.text

    olimpic = context.user_data.get("rating_olimpic", None)
    region = context.user_data.get("rating_region", None)
    district = context.user_data.get("rating_district", None)
    school = context.user_data.get("rating_school", None)
    class_room = context.user_data.get("rating_class", None)

    if text == _("🔙 Orqaga"):
        if not district:
            update.message.reply_text(
                _("Viloyatlardan birini tanlang"),
                reply_markup=default.region_btn(),
                parse_mode="HTML",
            )
            return state.REGION_RATING

        if not school:
            update.message.reply_text(
                _("Tuman yoki shahar"),
                reply_markup=default.district_rating(region),
                parse_mode="HTML",
            )
            return state.DISTRICT_RATING

        if not class_room:
            update.message.reply_text(
                _("Maktabni tanlang"),
                reply_markup=default.school_rating(district),
                parse_mode="HTML",
            )
            return state.SCHOOL_RATING

        update.message.reply_text(
            _("Sinfni tanlang"),
            reply_markup=default.class_room_rating(school),
            parse_mode="HTML",
        )
        return state.CLASS_ROOM_RATING

    olimpic = Olimpic.objects.get(id=context.user_data["rating_olimpic"])

    results = UserOlimpic.objects.filter(
        olimpic=olimpic,
        correct_answers__isnull=False,
        wrong_answers__isnull=False,
        not_answered__isnull=False,
        olimpic_duration__isnull=False,
    ).order_by("-correct_answers", "wrong_answers", "not_answered", "olimpic_duration"
               ).select_related("user")

    if region is not None:
        results = results.filter(user__region=region)

    if district is not None:
        results = results.filter(user__district=district)

    if school is not None:
        results = results.filter(user__school=school)

    if class_room is not None:
        results = results.filter(user__class_room=class_room)

    if not results:
        update.message.reply_text(
            _("Natijalar topilmadi"),
            reply_markup=default.back(),
        )
        return state.OLIMPIC_RATING_DETAIL

    text = _("{} - Natijalari\n\n").format(olimpic.title)
    user_result = results.filter(user=tg_user).first()
    query_result = list(results)

    if not user_result:
        text += _("Siz bu olimpiadada ishtirok etmadingiz\n\n")

    for result in results[:10]:
        text += _(
            "{index}) {full_name} - {correct_answers}/{wrong_answers}/{not_answered} - {olimpic_duration}\n"
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

    update.message.reply_text(
        text,
        reply_markup=default.back(),
        parse_mode="HTML",
    )
    return state.OLIMPIC_RATING_DETAIL


@get_member
def help(update: Update, context: CallbackContext, tg_user: models.TelegramProfile):
    update.message.reply_text(
        _("Sizda savollar bormi? Bizga yozing: @roboteachhelp"),
        parse_mode="HTML",
    )
