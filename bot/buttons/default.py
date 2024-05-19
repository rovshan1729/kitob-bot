from telegram import ReplyKeyboardMarkup, KeyboardButton
from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext_lazy, get_language
from django.core.cache import cache
from bot.models import TelegramButton, TelegramProfile
from common.models import Region, School, Class, District
from olimpic.models import Olimpic


def _(text):
    return str(gettext_lazy(text))


def language_btn():
    keyboards = []
    for lang in settings.LANGUAGES:
        keyboards.append(
            [
                _(lang[1])
            ]
        )
    return ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)


def back():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("🔙 Orqaga")),
            ]
        ],
        resize_keyboard=True
    )


def send_contact(is_back=True):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("📞 Telefon raqamni yuborish"), request_contact=True),
            ],
            [
                KeyboardButton(text=_("🔙 Orqaga")),
            ] if is_back else []
        ],
        resize_keyboard=True
    )


def region_btn(is_back=True):
    language = get_language().split('-')[0]
    keyboards = []
    if cache.get("main_region", None) is None:
        regions = Region.objects.filter(parent=None)
        cache.set("main_region", regions, 60 * 60 * 2)
    else:
        regions = cache.get("main_region")

    for index in range(0, regions.count(), 2):
        region = regions[index]
        if index + 1 == regions.count():

            keyboards.append(
                [
                    getattr(region, f"title_{language}")
                ]
            )
        else:
            keyboards.append(
                [
                    getattr(region, f"title_{language}"),
                    getattr(regions[index + 1], f"title_{language}")
                ]
            )

    if is_back:
        keyboards.append(
            [
                _("🔙 Orqaga"),
            ]
        )
    return ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)


def district_btn(region_id, is_back=True):
    language = get_language()
    print("REGGION", region_id)
    if cache.get(f"main_district_{region_id}", None) is None:
        districts = District.objects.filter(parent_id=region_id)
        cache.set(f"main_district_{region_id}", districts, 60 * 60 * 2)
    else:
        districts = cache.get(f"main_district_{region_id}")

    keyboards = []
    for index in range(0, districts.count(), 2):
        district = districts[index]
        if index + 1 == districts.count():
            keyboards.append(
                [
                    getattr(district, f'title_{language}')
                ]
            )
        else:
            keyboards.append(
                [
                    getattr(district, f'title_{language}'),
                    getattr(districts[index + 1], f'title_{language}')
                ]
            )

    if is_back:
        keyboards.append(
            [
                _("🔙 Orqaga"),
            ]
        )
    return ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)


def school_btn(district_id, is_back=True):
    language = get_language()
    if cache.get(f"main_school_{district_id}", None) is None:
        schools = School.objects.filter(district_id=district_id)
        cache.set(f"main_school_{district_id}", schools, 60 * 60 * 2)
    else:
        schools = cache.get(f"main_school_{district_id}")
    # schools = School.objects.filter(district_id=district_id)

    keyboards = []
    for index in range(0, schools.count(), 2):
        school = schools[index]
        if index + 1 == schools.count():
            keyboards.append(
                [
                    getattr(school, f'title_{language}')
                ]
            )
        else:
            keyboards.append(
                [
                    getattr(school, f'title_{language}'),
                    getattr(schools[index + 1], f'title_{language}')
                ]
            )

    if is_back:
        keyboards.append(
            [
                _("🔙 Orqaga"),
            ]
        )
    return ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)


def class_btn(is_back=True):
    keyboards = [
        [
            _("5-sinf"),
            _("6-sinf")
        ],
        [
            _("7-sinf"),
            _("8-sinf")
        ],
        [
            _("9-sinf"),
            _("10-sinf")
        ],
        [
            _("11-sinf"),
        ]
    ]

    if is_back:
        keyboards.append(
            [
                _("🔙 Orqaga"),
            ]
        )
    return ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)


def main_btn(bot_id):
    language = get_language().split('-')[0]
    keywords = [
        [
            _("Olimpiadaga kirish"),
            _("Olimpiada natijalarini ko’rish"),
        ]
    ]
    if cache.get(f"main_btn_{bot_id}", None) is None:
        buttons = TelegramButton.objects.filter(bot_id=bot_id, parent=None)
        cache.set(f"main_btn_{bot_id}", buttons, 60 * 60 * 2)
    else:
        buttons = cache.get(f"main_btn_{bot_id}")

    for index in range(0, len(buttons), 2):
        button = buttons[index]
        if index + 1 == len(buttons):
            keywords.append(
                [
                    getattr(button, f"title_{language}"),
                ]
            )
        else:
            keywords.append(
                [
                    getattr(button, f"title_{language}"),
                    getattr(buttons[index + 1], f"title_{language}")
                ]
            )

    keywords.append(
        [
            _("Olimpiada reytingini ko’rish"),
            _("Tilni alishtirish")
        ],
    )

    return ReplyKeyboardMarkup(keyboard=keywords, resize_keyboard=True)


def sub_btn(id):
    language = get_language()
    keywords = []
    buttons = TelegramButton.objects.filter(parent_id=id)
    for index in range(0, len(buttons), 2):
        button = buttons[index]
        if index + 1 == len(buttons):
            keywords.append(
                [
                    getattr(button, f"title_{language}")
                ]
            )
        else:
            keywords.append(
                [
                    getattr(button, f"title_{language}"),
                    getattr(buttons[index + 1], f"title_{language}")
                ]
            )

    keywords.append(
        [
            _("🔙 Orqaga"),
        ]
    )
    return ReplyKeyboardMarkup(keyboard=keywords, resize_keyboard=True)


def olimpics_btn(user_id):
    tg_user = TelegramProfile.objects.get(id=user_id)

    language = tg_user.language
    keyboards = []
    # olimpics = Olimpic.objects.filter(is_active=True)

    if cache.get(f"olimpics_{tg_user.region_id}_{tg_user.district_id}_{tg_user.school_id}_{tg_user.class_room}", None) is None:
        olimpics = Olimpic.objects.filter(is_active=True)

        if olimpics.filter(region__isnull=False).exists():
            olimpics = olimpics.filter(Q(region=tg_user.region) | Q(region__isnull=True))
        if olimpics.filter(district__isnull=False).exists():
            olimpics = olimpics.filter(Q(district=tg_user.district) | Q(district__isnull=True))
        if olimpics.filter(school__isnull=False).exists():
            olimpics = olimpics.filter(Q(school_id=tg_user.school_id) | Q(school__isnull=True))
        if olimpics.filter(class_room__isnull=False).exists():
            olimpics = olimpics.filter(Q(class_room=tg_user.class_room) | Q(class_room__isnull=True))
        cache.set(f"olimpics_{tg_user.region_id}_{tg_user.district_id}_{tg_user.school_id}_{tg_user.class_room}", olimpics, 60 * 30)
    else:
        olimpics = cache.get(f"olimpics_{tg_user.region_id}_{tg_user.district_id}_{tg_user.school_id}_{tg_user.class_room}")

    for index in range(0, olimpics.count(), 2):
        olimpic = olimpics[index]
        if index + 1 == olimpics.count():
            keyboards.append(
                [
                    getattr(olimpic, f"title_{language}")
                ]
            )
        else:
            keyboards.append(
                [
                    getattr(olimpic, f"title_{language}"),
                    getattr(olimpics[index + 1], f"title_{language}")
                ]
            )

    keyboards.append(
        [
            _("🔙 Orqaga"),
        ]
    )
    return ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)


def olimpic_btn():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=_("Testni boshlash"),
                )
            ],
            [
                KeyboardButton(
                    text=_("🔙 Orqaga"),
                )
            ]
        ],
        resize_keyboard=True
    )


def get_main():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                _("Bosh sahifa"),
            ]
        ],
        resize_keyboard=True
    )


def get_olimpics_result(user_id):
    tg_user = TelegramProfile.objects.get(id=user_id)
    language = tg_user.language
    keyboards = []
    if cache.get(f"olimpics_{tg_user.region_id}_{tg_user.district_id}_{tg_user.school_id}_{tg_user.class_room}", None) is None:
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


    for index in range(0, olimpics.count(), 2):
        olimpic = olimpics[index]
        if index + 1 == olimpics.count():
            keyboards.append(
                [
                    getattr(olimpic, f"title_{language}")
                ]
            )
        else:
            keyboards.append(
                [
                    getattr(olimpic, f"title_{language}"),
                    getattr(olimpics[index + 1], f"title_{language}")
                ]
            )
    keyboards.append(
        [
            _("🔙 Orqaga"),
        ]
    )
    return ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)


def get_certificate():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                _("Sertifikatni yuklab olish"),
            ],
            [
                _("🔙 Orqaga"),
            ]
        ],
        resize_keyboard=True
    )


def district_rating(region_id):
    keyboards = [
        [
            _("Reytingni ko'rish")
        ]
    ]

    if cache.get(f"district_{region_id}", None) is None:
        districts = District.objects.filter(parent_id=region_id)
        cache.set(f"district_{region_id}", districts, 60 * 60 * 2)
    else:
        districts = cache.get(f"district_{region_id}")

    for index in range(0, districts.count(), 2):
        district = districts[index]
        if index + 1 == districts.count():
            keyboards.append(
                [
                    district.title
                ]
            )
        else:
            keyboards.append(
                [
                    district.title,
                    districts[index + 1].title
                ]
            )

    keyboards.append(
        [
            _("🔙 Orqaga")
        ]
    )

    return ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)


def school_rating(district_id):
    keyboards = [
        [
            _("Reytingni ko'rish")
        ]
    ]
    if cache.get(f"school_{district_id}", None) is None:
        schools = School.objects.filter(district_id=district_id)
        cache.set(f"school_{district_id}", schools, 60 * 60 * 2)
    else:
        schools = cache.get(f"school_{district_id}")

    for index in range(0, schools.count(), 2):
        school = schools[index]
        if index + 1 == schools.count():
            keyboards.append(
                [
                    school.title
                ]
            )
        else:
            keyboards.append(
                [
                    school.title,
                    schools[index + 1].title
                ]
            )

    keyboards.append(
        [
            _("🔙 Orqaga")
        ]
    )

    return ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)


def class_room_rating(school_id):
    keyboards = [
        [
            _("Reytingni ko'rish")
        ],
        [
            _("5-sinf"),
            _("6-sinf")
        ],
        [
            _("7-sinf"),
            _("8-sinf")
        ],
        [
            _("9-sinf"),
            _("10-sinf")
        ],
        [
            _("11-sinf"),
        ]
    ]

    keyboards.append(
        [
            _("🔙 Orqaga")
        ]
    )

    return ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)
