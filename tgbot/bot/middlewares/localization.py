from aiogram import types
from typing import Tuple, Any

from aiogram.contrib.middlewares.i18n import I18nMiddleware
from tgbot.models import TelegramProfile

# LANG_STORAGE = {}
LANGS = ["ru", "en", "uz", "qr"]


class Localization(I18nMiddleware):
    async def get_user_locale(self, action: str, args: Tuple[Any]) -> str:
        """
        User locale getter
        You can override the method if you want to use different way of getting user language.
        :param action: event name
        :param args: event arguments
        :return: locale name
        """
        user: types.User = types.User.get_current()
        language_code = "uz"
        if user:
            user_data = TelegramProfile.objects.filter(telegram_id=user.id).first()
            language_code = user.language_code
            if user_data is None:
                TelegramProfile.objects.create(telegram_id=user.id, username=user.username, language=user.language_code)
            else:
                language_code = user_data.language
        *_, data = args
        language = data['locale'] = language_code
        return language
