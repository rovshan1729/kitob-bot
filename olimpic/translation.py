from modeltranslation.translator import TranslationOptions, register


from olimpic import models


@register(models.Olimpic)
class OlimpicTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(models.Question)
class QuestionTranslationOptions(TranslationOptions):
    fields = ("text",)


@register(models.Option)
class OptionTranslationOptions(TranslationOptions):
    fields = ("title",)
