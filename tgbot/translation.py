from modeltranslation.translator import register, TranslationOptions

from .models import RequiredGroup, TelegramButton


@register(RequiredGroup)
class RequiredGroupTranslationOption(TranslationOptions):
    fields = ("title",)


@register(TelegramButton)
class TelegramButtonTranslationOption(TranslationOptions):
    fields = ("title", "text")
    