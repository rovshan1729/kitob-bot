from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.models import Class
from tgbot.bot.loader import gettext as _
from bot.models import TelegramButton
from utils.bot import get_object_value


def main_markup(language="uz"):
    button_obj = TelegramButton.objects.filter(parent=None)
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(KeyboardButton(text=_("🏆 Olimpiadalar 🏆")), KeyboardButton(text=_("📈 Natijalar 📉")))
    button.add(*(KeyboardButton(text=get_object_value(button, "title", language)) for button in button_obj if
                 get_object_value(button, "title", language) is not None))
    button.add(KeyboardButton(text=_("🔝 Reyting 📊")), KeyboardButton(text=_("🌐 Tilni o'zgartirish")))
    return button


def generate_custom_markup(tg_buttons, language="uz"):
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(*(KeyboardButton(text=get_object_value(button, "title", language)) for button in tg_buttons if
                 get_object_value(button, "title", language) is not None))
    button.add(KeyboardButton(text=_("🔙 Orqaga")))
    return button


# main_markup.row("🏅 Mukofotlar 🎁", "ℹ️ Ma'lumotlar ℹ️")

main_menu_markup = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=_("🏠 Asosiy menyu")),
        ],
        [
            KeyboardButton(text=_("🔙 Orqaga"))
        ]
    ],
    resize_keyboard=True
)

start_olympic_markup = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=_("▶️ Testni boshlash")),
        ],
        [
            KeyboardButton(text=_("🔙 Orqaga"))
        ]
    ],
    resize_keyboard=True,
)

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=_("📞 Telefon raqamni yuborish"), request_contact=True),
        ],
        [
            KeyboardButton(text=_("🔙 Orqaga"))
        ]
    ],
    resize_keyboard=True,
)
back_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=_("🔙 Orqaga"))
        ]
    ],
    resize_keyboard=True,
)
check_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ To'gri"),
            KeyboardButton(text="♻️ Qayta kiritish"),
        ],
        [
            KeyboardButton(text="🛑 Bekor Qilish")
        ]
    ],
    resize_keyboard=True,
)

classes = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=_("5-sinf")),
        ],
        [
            KeyboardButton(text=_("6-sinf")),
            KeyboardButton(text=_("7-sinf"))
        ],
        [
            KeyboardButton(text=_("8-sinf")),
            KeyboardButton(text=_("9-sinf"))
        ],
        [
            KeyboardButton(text=_("10-sinf")),
            KeyboardButton(text=_("11-sinf"))
        ],
        [
            KeyboardButton(text="🔙 Orqaga"),
        ],
    ],
    resize_keyboard=True,
)


async def get_regions_markup(regions, language="uz"):
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(*(KeyboardButton(text=get_object_value(region, "title", language)) for region in regions if
                 get_object_value(region, "title", language) is not None))
    button.add(KeyboardButton(text=_("🔙 Orqaga")))
    return button


async def get_districts_markup(districts, language="uz"):
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(*(KeyboardButton(text=get_object_value(district, "title", language)) for district in districts if
                 get_object_value(district, "title", language) is not None))
    button.add(KeyboardButton(text=_("🔙 Orqaga")))
    return button


async def get_schools_markup(schools, language="uz"):
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(*(KeyboardButton(text=get_object_value(school, "title", language)) for school in schools if
                 get_object_value(school, "title", language) is not None))
    button.add(KeyboardButton(text=_("🔙 Orqaga")))
    return button


async def get_classes_markup():
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(*(KeyboardButton(text=class_room[1]) for class_room in Class))
    button.add(KeyboardButton(text=_("🔙 Orqaga")))
    return button


async def get_olympics_markup(olympics, language="uz"):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(*(KeyboardButton(text=get_object_value(olympic, "title", language)) for olympic in olympics if
                 get_object_value(olympic, "title", language) is not None))
    markup.add(KeyboardButton(text=_("🔙 Orqaga")))
    return markup
