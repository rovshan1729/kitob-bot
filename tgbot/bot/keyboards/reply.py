from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from tgbot.bot.loader import gettext as _
from tgbot.models import TelegramButton
from utils.bot import get_object_value


def main_markup(language="uz"):
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(KeyboardButton(text=_("Bosh menyu")), KeyboardButton(text=_("🌐 Tilni o'zgartirish")))
    return button 


def select_plan(button_obj, language="uz"):
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(*(KeyboardButton(text=get_object_value(button, "title", language)) for button in button_obj if
                 get_object_value(button, "title", language) is not None))
    button.add(KeyboardButton(text=_('🔙 Orqaga')))
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


def plan_button(button_obj, language="uz"):
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(*(KeyboardButton(text=get_object_value(button, "title", language)) for button in button_obj if
                 get_object_value(button, "title", language) is not None))
    button.add(KeyboardButton(text=_('🔙 Orqaga')))
    return button