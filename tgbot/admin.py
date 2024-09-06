from django.contrib import admin

from . import models
from tgbot.mixins import TabbedTranslationAdmin, TranslationRequiredMixin
# Register your models here.

admin.site.register(models.TelegramBot)

@admin.register(models.Skill)
class SkillAdmin(TabbedTranslationAdmin):
    list_display = ('id', 'title')
    

@admin.register(models.SelectPlan)
class SelectPlan(TabbedTranslationAdmin):
    list_display = ('id', 'title', 'parent')
    
@admin.register(models.PlanButtons)
class PlanContent(TabbedTranslationAdmin):
    list_display = ("id", "title", "plan")


@admin.register(models.TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_id", "username", "language",)
    list_display_links = ("id", 'telegram_id', "username")
    list_filter = ("language", "is_registered",)
    search_fields = ("username", "telegram_id")
    list_per_page = 20


@admin.register(models.RequiredGroup)
class RequiredGroupAdmin(TabbedTranslationAdmin, TranslationRequiredMixin):
    list_display = ("id", "bot", "title", "chat_id", "created_at", "updated_at")
    list_display_links = ("id", "title", "bot")
    search_fields = ("bot", "title", "chat_id")
    list_per_page = 20


class TelegramButtonInline(admin.StackedInline):
    model = models.TelegramButton
    extra = 1

@admin.register(models.TelegramButton)
class TelegramButtonAdmin(TranslationRequiredMixin, TabbedTranslationAdmin):
    list_display = ("id", "title", 'text', "parent", "created_at", "updated_at")
    list_display_links = ("id", 'title', "text")
    search_fields = ("text", "title", "parent__title")
    list_per_page = 20

    inlines = [TelegramButtonInline]