from django.contrib import admin

from . import models
from tgbot.mixins import TabbedTranslationAdmin, TranslationRequiredMixin

admin.site.register(models.TelegramBot)


@admin.register(models.TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "username", "full_name", "language", "is_admin")
    list_display_links = ("id", "username")
    list_filter = ("language", "is_registered", "is_admin")
    search_fields = ("username", "full_name")


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
    list_display = ('id', 'user', 'book', 'pages_read')
    search_fields = ('user__username', 'user__full_name')
    readonly_fields= ("created_at",)
    

@admin.register(models.DailyMessage)
class DailyMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "message")


@admin.register(models.Group)
class GroupAdmin(TabbedTranslationAdmin):
    list_display = ("id", "title", "created_at")
    list_display_links = ("id", "title")


@admin.register(models.ReportMessage)
class GroupAdmin(TabbedTranslationAdmin):
    list_display = ("id", "group", "message_id", "last_update")
    list_display_links = ("id",)


@admin.register(models.ConfirmationReport)
class ConfirmationReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'date', 'pages_read')
    search_fields = ('user__username', 'user__full_name')


@admin.register(models.LastTopicID)
class LastTopicIDAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic_id')


@admin.register(models.BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'blocked_at')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'user__full_name')

