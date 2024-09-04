from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel
from common.managers import DistrictManager, RegionManager
from django.core.exceptions import ValidationError

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        abstract = True


class VersionHistory(BaseModel):
    version = models.CharField(_("Version"), max_length=64)
    required = models.BooleanField(_("Required"), default=True)

    class Meta:
        verbose_name = _("Version history")
        verbose_name_plural = _("Version histories")

    def __str__(self):
        return self.version


class FrontendTranslation(BaseModel):
    key = models.CharField(_("Key"), max_length=255, unique=True)
    text = models.CharField(_("Text"), max_length=1024)

    class Meta:
        verbose_name = _("Frontend translation")
        verbose_name_plural = _("Frontend translations")

    def __str__(self):
        return str(self.key)


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


class Region(BaseModel):
    title = models.CharField(_("Name"), max_length=255)
    parent = models.ForeignKey("self", related_name="regions", on_delete=models.CASCADE, blank=True, null=True,)

    objects = RegionManager()

    def save(self, *args, **kwargs):
        if not self.title_uz:
            self.title_uz = self.title
        if not self.title_ru:
            self.title_ru = self.title
        if not self.title_en:
            self.title_en = self.title
        super().save(*args, **kwargs)

    def clean(self):
        if not self.title:
            raise ValidationError(_("Title is required"))

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")

    def __str__(self):
        return self.title


class District(Region):
    objects = DistrictManager()

    def save(self, *args, **kwargs):
        if not self.title_uz:
            self.title_uz = self.title
        if not self.title_ru:
            self.title_ru = self.title
        if not self.title_en:
            self.title_en = self.title
        super(District, self).save(*args, **kwargs)

    def clean(self):
        if not self.title:
            raise ValidationError(_("Title is required"))

    def __str__(self):
        return self.title

    class Meta:
        proxy = True
        verbose_name = _("District")
        verbose_name_plural = _("Districts")



class School(BaseModel):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="schools")
    title = models.CharField(_("Name"), max_length=255)

    def save(self, *args, **kwargs):
        if not self.title_uz:
            self.title_uz = self.title
        if not self.title_ru:
            self.title_ru = self.title
        if not self.title_en:
            self.title_en = self.title
        super().save(*args, **kwargs)

    def clean(self):
        if not self.title:
            raise ValidationError(_("Title is required"))

    def __str__(self):
        return f"{self.title}"


Class = (
    ("5-sinf", _("5-sinf")),
    ("6-sinf", _("6-sinf")),
    ("7-sinf", _("7-sinf")),
    ("8-sinf", _("8-sinf")),
    ("9-sinf", _("9-sinf")),
    ("10-sinf", _("10-sinf")),
    ("11-sinf", _("11-sinf")),
)


class Settings(SingletonModel):
    site_name = models.CharField(_("Site name"), max_length=255, blank=True, null=True)
    site_logo = models.ImageField(_("Site logo"), upload_to="uploads/%Y/%m/%d/", blank=True, null=True)

    bot_token = models.CharField(_("Bot token"), max_length=255, blank=True, null=True)
    host_url = models.URLField(_("Host URL"), blank=True, null=True)

    def __str__(self):
        return "Settings"

    class Meta:
        verbose_name = _("Settings")
