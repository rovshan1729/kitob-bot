from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from tgbot.bot.loader import gettext as _
from tgbot.models import TelegramButton
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


async def get_result_markup(is_end_time: bool):
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    if is_end_time:
        markup.add(KeyboardButton(text=_("⬇️ Sertifikatni yuklab olish")))
    markup.add(KeyboardButton(text=_("🔙 Orqaga")))
    return markup


async def rating_back():
    button = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button.add(KeyboardButton(text=_("🔙 Orqaga")))
    return button