from django.contrib import admin

from bot import models
from bot.forms import RequiredGroupForm
from common.mixins import TabbedTranslationAdmin, TranslationRequiredMixin
# Register your models here.

admin.site.register(models.TelegramBot)
# admin.site.register(models.TelegramProfile)

@admin.register(models.TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_id", "first_name", "last_name", "username", "language", "region", 'district', 'school', 'class_room',)
    list_display_links = ("id", 'telegram_id', "first_name", "last_name", "username")
    list_filter = ("language", "is_registered", "is_olimpic", "region", "district", "school", "class_room",)
    search_fields = ("first_name", "last_name", "username", "telegram_id", "region__title", "district__title", "school__title",)
    list_per_page = 20
    list_select_related = ("region", "district", "school", )

    actions = ["is_olimpic_action",]

    def is_olimpic_action(self, request, queryset):
        queryset.update(is_olimpic=False)

    def get_district_title(self, obj):
        if obj.region is None:
            return "-"
        return f"{obj.region.title or ''} {obj.district.title or ''}"

    def get_school_title(self, obj):
        if obj.district is None:
            return "-"
        return f"{obj.school.district.title or ''} {obj.school.title or ''}"

    get_school_title.short_description = "School"
    get_district_title.short_description = "District"

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


@admin.register(models.Notification)
class NotificatoinAdmin(TabbedTranslationAdmin, TranslationRequiredMixin):
    list_display = ("id", "bot", "title", "created_at", "updated_at")
    list_display_links = ("id", "title", "bot")
    search_fields = ("bot", "title")
    list_per_page = 20

    # filter_horizontal = ("users",