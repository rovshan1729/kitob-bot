from modeltranslation.translator import register, TranslationOptions

from .models import RequiredGroup, TelegramButton, Skill


@register(RequiredGroup)
class RequiredGroupTranslationOption(TranslationOptions):
    fields = ("title",)


@register(TelegramButton)
class TelegramButtonTranslationOption(TranslationOptions):
    fields = ("title", "text")
    

@register(Skill)
class SkillTranslationOption(TranslationOptions):
    fields = ('title',)