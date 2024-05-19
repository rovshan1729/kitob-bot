from modeltranslation.translator import register, TranslationOptions

from bot.models import RequiredGroup, TelegramButton, Notification


@register(RequiredGroup)
class RequiredGroupTranslationOption(TranslationOptions):
    fields = ("title",)


@register(TelegramButton)
class TelegramButtonTranslationOption(TranslationOptions):
    fields = ("title", "text")


@register(Notification)
class NotificationTranslationOption(TranslationOptions):
    fields = ("title", "text")