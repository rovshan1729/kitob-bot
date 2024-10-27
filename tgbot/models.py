from unittest.mock import numerics

from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

from django.conf import settings
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField
from auditlog.registry import auditlog

from utils.bot import set_webhook_request, get_info
from utils.validate_supported_tags import is_valid_content, validate_content
from django.utils import timezone


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        abstract = True  
          

class Media(BaseModel):
    class MediaType(models.TextChoices):
        VIDEO = "video", _("Video")
        IMAGE = "image", _("Image")

    id = models.UUIDField(primary_key=True, editable=False)
    file = models.FileField(_("File"), upload_to="uploads/%Y/%m/%d/")
    file_type = models.CharField(_("File Type"), choices=MediaType.choices)

    class Meta:
        db_table = "Media"
        verbose_name = _("Media")
        verbose_name_plural = _("Media")

    def save(self, *args, **kwargs):
        if self.file.name.split(".")[-1] in ["jpg", "jpeg", "png", "gif"]:
            self.file_type = Media.MediaType.IMAGE
        elif self.file.name.split(".")[-1] in ["mp4", "avi", "mkv", "mov"]:
            self.file_type = Media.MediaType.VIDEO
        super(Media, self).save(*args, **kwargs)

    def __str__(self):
        return self.file.name


class Settings(SingletonModel):
    site_name = models.CharField(_("Site name"), max_length=255, blank=True, null=True)
    site_logo = models.ImageField(_("Site logo"), upload_to="uploads/%Y/%m/%d/", blank=True, null=True)

    bot_token = models.CharField(_("Bot token"), max_length=255, blank=True, null=True)
    host_url = models.URLField(_("Host URL"), blank=True, null=True)

    def __str__(self):
        return "Settings"

    class Meta:
        verbose_name = _("Settings")


class TelegramBot(BaseModel):
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


class Group(BaseModel):
    title = models.CharField(max_length=255, verbose_name=_("Group name"))
    topic_id = models.CharField(max_length=255, verbose_name=_("Topic ID"))
    chat_id = models.CharField(max_length=255, verbose_name=_("Chat ID"), default="-1002237773868")

    ordering = models.IntegerField(_("Ordering"), default=1)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "groups"
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")


class TelegramProfile(BaseModel):
    bot = models.ForeignKey(TelegramBot, models.CASCADE, null=True)
    telegram_id = models.PositiveBigIntegerField()
    username = models.CharField(max_length=255, null=True, blank=True)
    language = models.CharField(
        max_length=255, choices=settings.LANGUAGES, null=True, blank=True)

    full_name = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Full Name"))
    phone_number = models.CharField(max_length=128, blank=True, null=True, verbose_name=_("Phone Number"))
    group = models.ForeignKey(Group, models.CASCADE, null=True, blank=True, verbose_name=_("Group"))

    is_registered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} {self.username} {self.telegram_id}"

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

    class Meta:
        verbose_name = _("Required Chats")
        verbose_name_plural = _("Required Chats")
        db_table = "required_groups"


class TelegramButton(BaseModel):
    bot = models.ForeignKey(TelegramBot, models.CASCADE, verbose_name=_("Telegram Bot"))
    parent = models.ForeignKey("self", models.CASCADE, blank=True, null=True)

    title = models.CharField(max_length=255, verbose_name=_("Button Name"))
    text = RichTextField(verbose_name=_("Button Text"), blank=True, null=True)
    content = models.FileField(upload_to="buttons", verbose_name=_("Button Content"), blank=True, null=True)
    file_id = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("File ID"))

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.title_uz:
            self.title_uz = self.title
        if not self.title_ru:
            self.title_ru = self.title

        if not self.text_uz:
            self.text_uz = self.text
        if not self.text_ru:
            self.text_ru = self.text

        if self.text_ru:
            self.text_ru = validate_content(self.text_ru)
        if self.text_uz:
            self.text_uz = validate_content(self.text_uz)
        super(TelegramButton, self).save(*args, **kwargs)
        

class BookReport(BaseModel):
    user = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, verbose_name=_("User"))
    reading_day = models.IntegerField(default=1, verbose_name=_("Reading day"))
    book = models.CharField(max_length=255, verbose_name=_("Book title"))
    pages_read = models.IntegerField(default=1, verbose_name=_("Pages read"))
    
    def __str__(self):
        return f'{self.user.username}: {self.reading_day}-kun {self.book}. {self.pages_read}+ bet.'
    

class ReportMessage(models.Model):
    chat_id = models.CharField(max_length=255)
    group = models.ForeignKey(Group, models.CASCADE, null=True, blank=True, verbose_name=_("Group"))
    message_id = models.PositiveIntegerField(null=True, blank=True)
    message_text = models.TextField(null=True, blank=True)
    last_update = models.DateField(default=timezone.now)
    message_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Message {self.message_id} in chat {self.chat_id}"


class ConfirmationReport(models.Model):
    user = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, verbose_name=_("User"))
    reading_day = models.IntegerField()
    book = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    pages_read = models.IntegerField()

    def __str__(self):
        return f"User {self.user.full_name} readed {self.pages_read} pages"


class LastTopicID(SingletonModel):
    topic_id = models.CharField(max_length=255, verbose_name=_("Topic ID"))

    def __str__(self):
        return self.topic_id


class DailyMessage(models.Model):
    message = models.TextField(verbose_name=_("Message"), default="Notification")

    def __str__(self):
        return self.message

    class Meta:
        verbose_name = _("Daily Message")
        verbose_name_plural = _("Daily Messages")


class BlockedUser(models.Model):
    user = models.ForeignKey(TelegramProfile, models.CASCADE, verbose_name=_("Blocked User"))
    blocked_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Blocked At"))

    class Meta:
        verbose_name = _("Blocked User")
        verbose_name_plural = _("Blocked Users")

    def __str__(self):
        return f"{self.user.full_name} (Blocked)"



auditlog.register(RequiredGroup)
auditlog.register(TelegramProfile)
auditlog.register(TelegramBot)
