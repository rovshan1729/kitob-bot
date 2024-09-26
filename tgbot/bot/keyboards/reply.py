from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from tgbot.bot.loader import gettext as _


def confirm_markup(language="uz"):
    button = ReplyKeyboardMarkup(resize_keyboard=True)
    button.add(KeyboardButton(_("Tasdiqlash")), KeyboardButton(_("Bekor qilish")))
    return button


def main_markup(language="uz"):
    if language == "uz":
        content = "Kitob hisoboti1"
        lang = "🌐 Tilni o'zgartirish1"
    elif language == "ru":
        content = "Отчет о книге1"
        lang = "🌐 Изменить язык1"
    else:
        content = "Kitob hisoboti2"
        lang = "🌐 Tilni o'zgartirish2"
        
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(KeyboardButton(text=content), KeyboardButton(text=lang))
    return button 

    
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
