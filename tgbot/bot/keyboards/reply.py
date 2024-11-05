from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from tgbot.bot.loader import gettext as _
from tgbot.models import TelegramButton, Group
from utils.bot import get_object_value


def confirm_markup(language="uz"):
    button = ReplyKeyboardMarkup(resize_keyboard=True)
    button.add(KeyboardButton(_("Tasdiqlash")), KeyboardButton(_("Bekor qilish")))
    return button


def group_markup(language="uz"):
    button_obj = Group.objects.all()
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(*(KeyboardButton(text=get_object_value(button, "title", language)) for button in button_obj if
                 get_object_value(button, "title", language) is not None))
    return button


def main_markup(language="uz"):
    if language == "uz":
        content = "📚 Kitob hisoboti"
        lang = "🌐 Tilni o'zgartirish"
        group = "👤 Guruhni o'zgartirish"

    elif language == "ru":
        content = "📚 Отчет о книге"
        lang = "🌐 Изменить язык"
        group = "👤 Изменить группу"
    else:
        content = "📚 Kitob hisoboti"
        lang = "🌐 Tilni o'zgartirish"
        group = "👤 Guruhni o'zgartirish"
        
    button = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button.add(KeyboardButton(text=content), KeyboardButton(text=lang), KeyboardButton(text=group))
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

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=_("✅ Ro'yhatdan o'tganlar")),
            KeyboardButton(text=_("❌ Ro'yhatdan o'tmaganlar"))
        ],
        [
            KeyboardButton(text=_("👨‍👩‍👦‍👦 Barcha foydalanuvchilar")),
            KeyboardButton(text=_("📊 Statistikani ko'rish"))
        ]
    ],
    resize_keyboard=True,
)
