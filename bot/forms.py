from django import forms
from django.utils.translation import gettext_lazy as _
from telegram import Bot
from telegram.error import BadRequest

from bot.models import RequiredGroup

class RequiredGroupForm(forms.ModelForm):
    class Meta:
        model = RequiredGroup
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        tg_bot = cleaned_data.get("bot")

        chat_id = cleaned_data.get("chat_id")
        bot = Bot(token=tg_bot.bot_token)
        try:
            chat = bot.get_chat_administrators(chat_id=chat_id)
            for member in chat:
                if member['user']['username'] == tg_bot.bot_username:
                    return cleaned_data

            # Bot is not admin in this chat
            raise forms.ValidationError(_("Bot is not admin in this chat"))
        except BadRequest as e:
            raise forms.ValidationError(_("Chat not found"))

