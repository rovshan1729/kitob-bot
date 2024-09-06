from modeltranslation.translator import register, TranslationOptions

from .models import RequiredGroup, TelegramButton, Skill, SelectPlan, PlanButtons


@register(RequiredGroup)
class RequiredGroupTranslationOption(TranslationOptions):
    fields = ("title",)


@register(TelegramButton)
class TelegramButtonTranslationOption(TranslationOptions):
    fields = ("title", "text")
    

@register(Skill)
class SkillTranslationOption(TranslationOptions):
    fields = ('title',)
    

@register(SelectPlan)
class SelectPlanTranslationOption(TranslationOptions):
    fields = ('title', 'content')
    

@register(PlanButtons)
class PlanButtonTranslationOption(TranslationOptions):
    fields = ('title', 'content')
    