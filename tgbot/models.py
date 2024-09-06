from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

from django.conf import settings
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField
from auditlog.registry import auditlog

from telegram import Bot
from telegram.error import BadRequest

from utils.bot import set_webhook_request, get_info
from utils.validate_supported_tags import is_valid_content, validate_content

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


class TelegramProfile(BaseModel):
    bot = models.ForeignKey(TelegramBot, models.CASCADE, null=True)
    telegram_id = models.PositiveBigIntegerField()
    username = models.CharField(max_length=255, null=True, blank=True)
    language = models.CharField(
        max_length=255, choices=settings.LANGUAGES, null=True, blank=True)

    full_name = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Full Name"))
    phone_number = models.CharField(max_length=128, blank=True, null=True, verbose_name=_("Phone Number"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
    plan = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("User Plan"))
    skill = models.ManyToManyField("tgbot.Skill")

    is_registered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} {self.username} {self.telegram_id}"

    class Meta:
        verbose_name = "Telegram Profile"
        verbose_name_plural = "Telegram Profiles"
        db_table = "telegram_profiles"
        
        
class Skill(BaseModel):
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Skill"))
    
    parent = models.ForeignKey('self', models.CASCADE, blank=True, null=True, verbose_name=_("Parent"),
                               related_name="child")
    
            
    def __str__(self):
        return self.title


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
        
class SelectPlan(BaseModel):
    title = models.CharField(max_length=255)
    
    class AnswerChoice(models.TextChoices):
        TEXT_BUTTON = "text_button", "Text Button"
        TEXT_CV_LINK = "text_cv_link", "Text CV Link"
        TEXT_LINK = "text_link", "Text Link"
         
    type = models.CharField(
        max_length=50,  
        choices=AnswerChoice.choices,
        blank=True,
        null=True,
        help_text="Type of action for this plan (button, CV link, or regular link)."
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='children', 
        help_text="Parent plan, if this is a sub-plan."
    )
    
    content = models.TextField(verbose_name=_("Content"), null=True)
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Link"))
    
    def __str__(self):
        return self.title
    
class PlanButtons(BaseModel):
    plan = models.ForeignKey(SelectPlan, on_delete=models.CASCADE, related_name="buttons")
    title = models.CharField(max_length=128, verbose_name=_("Keyboard name"))
    content = models.TextField(verbose_name=_("Content"))
    link = models.URLField(blank=True, null=True, verbose_name=_("Link"))
    
    def __str__(self):
        return self.title
    


auditlog.register(RequiredGroup)
auditlog.register(TelegramProfile)
auditlog.register(TelegramBot)
