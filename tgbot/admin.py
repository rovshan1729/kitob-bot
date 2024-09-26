from django.contrib import admin

from . import models
from tgbot.mixins import TabbedTranslationAdmin, TranslationRequiredMixin
# Register your models here.

admin.site.register(models.TelegramBot)


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
    

@admin.register(models.BookReport)
class BookReportAdmin(admin.ModelAdmin):
    readonly_fields= ("created_at",)
    

@admin.register(models.DailyMessage)
class DailyMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "message")