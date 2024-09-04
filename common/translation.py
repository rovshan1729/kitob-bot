# translation.py
from modeltranslation.translator import TranslationOptions, register

from . import models


@register(models.FrontendTranslation)
class FrontTranslationOptions(TranslationOptions):
    fields = ("text",)
# Loyiha qanday tillarda bo'lishiga qarab settings dan tillar qoshilgandan keyin migratsiya qilinsin


@register(models.Region)
class RegionTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(models.District)
class RegionTranslationOptions(TranslationOptions):
    fields = ("title",)

@register(models.School)
class SchoolTranslationOptions(TranslationOptions):
    fields = ("title",)