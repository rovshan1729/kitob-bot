from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField
from telegram import Bot
from telegram.error import BadRequest
from auditlog.registry import auditlog

from utils.bot import set_webhook_request, get_info
from common.models import BaseModel, Class
from utils.validate_supported_tags import is_valid_content, validate_content


class TelegramBot(models.Model):
    name = models.CharField(max_length=30, null=True, blank=True)
    bot_token = models.CharField(max_length=255)
    bot_username = models.CharField(max_length=125, blank=True, null=True)

    def save(self, *args, **kwargs):
        set_webhook_request(self.bot_token)
        username, name = get_info(bot_token=self.bot_token)
        self.bot_username = username
        self.name = name
        super(TelegramBot, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Telegram Bot")
        verbose_name_plural = _("Telegram Bots")
        db_table = "telegram_bots"


class TelegramProfile(BaseModel):
    bot = models.ForeignKey(TelegramBot, models.CASCADE, null=True)
    telegram_id = models.PositiveBigIntegerField()
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    language = models.CharField(
        max_length=255, choices=settings.LANGUAGES, null=True, blank=True)

    full_name = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Full Name"))
    phone_number = models.CharField(max_length=128, blank=True, null=True, verbose_name=_("Phone Number"))
    birth_day = models.DateField(blank=True, null=True, verbose_name=_("Bith Day"))

    region = models.ForeignKey('common.Region', models.CASCADE, blank=True, null=True, verbose_name=_("Region"),
                               related_name="region")
    district = models.ForeignKey("common.District", models.CASCADE, blank=True, null=True, verbose_name=_("District"))
    school = models.ForeignKey("common.School", models.CASCADE, blank=True, null=True, verbose_name=_("School"))
    class_room = models.CharField(max_length=255, blank=True, null=True, choices=Class, verbose_name=_("Class Room"))
    is_registered = models.BooleanField(default=False)

    is_olimpic = models.BooleanField(default=False, editable=False)
    _user_data = models.JSONField(blank=True, null=True, verbose_name=_("User Data"), editable=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.username} {self.telegram_id}"

    class Meta:
        verbose_name = "Telegram Profile"
        verbose_name_plural = "Telegram Profiles"
        db_table = "telegram_profiles"


class RequiredGroup(BaseModel):
    chat_id = models.CharField(max_length=255, verbose_name=_("Chat ID or Username"),
                               help_text=_("Chat ID: -100000000 or Username: @username"))
    title = models.CharField(max_length=255, null=True, blank=True)
    bot = models.ForeignKey(TelegramBot, models.CASCADE)

    def __str__(self):
        return f"{self.chat_id} - {self.bot.name}"

    # def clean(self):
    #     chat_id = self.chat_id
    #     bot = Bot(token=self.bot.bot_token)
    #     if not self.title_uz or not self.title_ru or not self.title_en:
    #         chat_title = bot.get_chat(chat_id=chat_id).title
    #         self.title_uz = chat_title
    #         self.title_ru = chat_title
    #         self.title_en = chat_title
    #     try:
    #         chat = bot.get_chat_administrators(chat_id=chat_id)
    #         for member in chat:
    #             if member['user']['username'] == self.bot.bot_username:
    #                 return super().clean()
    #
    #         # Bot is not admin in this chat
    #         raise ValidationError(_("Bot is not admin in this chat"))
    #     except BadRequest as e:
    #         raise ValidationError(_("Chat not found"))

    class Meta:
        verbose_name = _("Required Chats")
        verbose_name_plural = _("Required Chats")
        db_table = "required_groups"


class TelegramButton(BaseModel):
    bot = models.ForeignKey(TelegramBot, models.CASCADE, verbose_name=_("Telegram Bot"))
    parent = models.ForeignKey("self", models.CASCADE, blank=True, null=True)

    title = models.CharField(max_length=255, verbose_name=_("Button Name"))
    text = RichTextField(verbose_name=_("Button Text"))
    content = models.FileField(upload_to="buttons", verbose_name=_("Button Content"), blank=True, null=True)
    file_id = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("File ID"))

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not is_valid_content(self.text_en) and not is_valid_content(self.text_ru) and not is_valid_content(
                self.text_uz):
            raise ValidationError(_("Invalid content"))

        if not self.title_uz:
            self.title_uz = self.title
        if not self.title_ru:
            self.title_ru = self.title
        if not self.title_en:
            self.title_en = self.title

        if not self.text_uz:
            self.text_uz = self.text
        if not self.text_ru:
            self.text_ru = self.text
        if not self.text_en:
            self.text_en = self.text

        if self.text_en:
            self.text_en = validate_content(self.text_en)
        if self.text_ru:
            self.text_ru = validate_content(self.text_ru)
        if self.text_uz:
            self.text_uz = validate_content(self.text_uz)
        super(TelegramButton, self).save(*args, **kwargs)

    def clean(self):
        if not self.title:
            raise ValidationError(_("Title is required"))
        if not self.text:
            raise ValidationError(_("Text is required"))

    class Meta:
        verbose_name = _("Telegram Button")
        verbose_name_plural = _("Telegram Buttons")
        db_table = "telegram_buttons"


class Notification(BaseModel):
    bot = models.ForeignKey(TelegramBot, models.CASCADE, verbose_name=_("Telegram Bot"))
    users = models.ManyToManyField(TelegramProfile, verbose_name=_("Users"), blank=True)
    region = models.ForeignKey("common.Region", models.CASCADE, verbose_name=_("Region"),
                               related_name="notification_region", null=True, blank=True)
    district = models.ForeignKey("common.District", models.CASCADE, verbose_name=_("District"),
                                 related_name='notification_district', null=True, blank=True)
    school = models.ForeignKey("common.School", models.CASCADE, verbose_name=_("School"), null=True, blank=True)
    class_room = models.CharField(max_length=255, blank=True, null=True, choices=Class, verbose_name=_("Class Room"))
    is_all_users = models.BooleanField(default=False, verbose_name=_("Is All Users"))

    is_not_registered = models.BooleanField(default=False, verbose_name=_("Is Not Registered"))

    title = models.CharField(max_length=255, verbose_name=_("Notification Title"))
    text = RichTextField(verbose_name=_("Notification Text"))
    file_content = models.FileField(upload_to="notifications", verbose_name=_("Notification File Content"), blank=True,
                                    null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.title_uz:
            self.title_uz = self.title
        if not self.title_ru:
            self.title_ru = self.title
        if not self.title_en:
            self.title_en = self.title

        if not self.text_uz:
            self.text_uz = self.text
        if not self.text_ru:
            self.text_ru = self.text
        if not self.text_en:
            self.text_en = self.text

        if self.text_uz:
            self.text_uz = validate_content(self.text_uz)
        if self.text_ru:
            self.text_ru = validate_content(self.text_ru)
        if self.text_en:
            self.text_en = validate_content(self.text_en)

        super(Notification, self).save(*args, **kwargs)

    def clean(self):
        if not self.title:
            raise ValidationError(_("Title is required"))

        if not self.text:
            raise ValidationError(_("Text is required"))

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        db_table = "notifications"


auditlog.register(RequiredGroup)
auditlog.register(TelegramProfile)
auditlog.register(TelegramBot)
