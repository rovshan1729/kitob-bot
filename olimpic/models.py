from uuid import uuid4
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField
from django_celery_beat.models import PeriodicTask, IntervalSchedule, ClockedSchedule

from auditlog.registry import auditlog

from common.models import BaseModel, Class
from utils.validate_supported_tags import is_valid_content, validate_content


# Create your models here.


class Olimpic(BaseModel):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = RichTextField(verbose_name=_("Description"))
    image = models.ImageField(upload_to="olimpics", null=True, blank=True)
    file_id = models.CharField(max_length=255, null=True, blank=True)
    start_time = models.DateTimeField(verbose_name=_("Start Time"), db_index=True)
    end_time = models.DateTimeField(verbose_name=_("End Time"), db_index=True)
    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"), db_index=True)
    result_publish = models.DateTimeField(null=True, verbose_name=_("Result Publish"), db_index=True)
    certificate_generate = models.DateTimeField(null=True, verbose_name=_("Certificate Generate"), db_index=True)

    is_all_users = models.BooleanField(default=False, verbose_name=_("Is All Users"), db_index=True)
    region = models.ForeignKey("common.Region", models.CASCADE, blank=True, null=True, related_name="olimpic_regions",
                               verbose_name=_("Region"))
    district = models.ForeignKey("common.District", models.CASCADE, blank=True, null=True,
                                 related_name="olimpic_districts", verbose_name=_("District"))
    school = models.ForeignKey("common.School", models.CASCADE, blank=True, null=True, related_name="olimpic_schools",
                               verbose_name=_("School"))
    class_room = models.CharField(max_length=255, blank=True, null=True, choices=Class, verbose_name=_("Class Room"),
                                  db_index=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.title:
            raise ValidationError(_("Title is required"))

    #
    #     if not self.description:
    #         raise ValidationError(_("Description is required"))
    #
    #     if not is_valid_content(self.description_uz) and not is_valid_content(
    #             self.description_ru) and not is_valid_content(self.description_en):
    #         raise ValidationError(_("Invalid content"))
    #
    #     if not self.title_uz:
    #         self.title_uz = self.title
    #     if not self.title_ru:
    #         self.title_ru = self.title
    #     if not self.title_en:
    #         self.title_en = self.title
    #
    #     if not self.description_uz:
    #         self.description_uz = self.description
    #     if not self.description_ru:
    #         self.description_ru = self.description
    #     if not self.description_en:
    #         self.description_en = self.description
    #
    #     self.description_uz = validate_content(self.description_uz)
    #     self.description_ru = validate_content(self.description_ru)
    #     self.description_en = validate_content(self.description_en)

        # schedule, created = ClockedSchedule.objects.get_or_create(
        #     clocked_time=self.certificate_generate,
        # )
        #
        # PeriodicTask.objects.get_or_create(
        #     clocked=schedule,
        #     name=f"Olimpic certificate {self.id} {uuid4()}",
        #     task="apps.olimpic.tasks.generate_certificates",
        #     args=f"[{self.id}]",
        #     start_time=self.certificate_generate,
        #     one_off=True,
        # )
        super(Olimpic, self).save(*args, **kwargs)


class Question(BaseModel):
    olimpic = models.ForeignKey(Olimpic, models.CASCADE, related_name="questions")

    text = RichTextField(verbose_name=_("Text"))
    duration = models.PositiveIntegerField(default=0, verbose_name=_("Duration (seconds)"))
    image = models.ImageField(upload_to="questions", null=True, blank=True)
    file_content = models.FileField(upload_to="questions", null=True, blank=True)

    def __str__(self):
        return str(self.text)

    def save(self, *args, **kwargs):
        if not self.text:
            raise ValidationError(_("Text is required"))

        if not is_valid_content(self.text_uz) and not is_valid_content(self.text_ru) and not is_valid_content(
                self.text_en):
            raise ValidationError(_("Invalid content"))

        if not self.text_uz:
            self.text_uz = self.text
        if not self.text_ru:
            self.text_ru = self.text
        if not self.text_en:
            self.text_en = self.text

        self.text_uz = validate_content(self.text_uz)
        self.text_ru = validate_content(self.text_ru)
        self.text_en = validate_content(self.text_en)

        super(Question, self).save(*args, **kwargs)


class OlimpicCertifeicate(BaseModel):
    olimpic = models.OneToOneField(Olimpic, models.CASCADE, related_name="certificate")
    certificate = models.ImageField(upload_to="certificates", null=True, blank=True)


class Option(BaseModel):
    title = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False, db_index=True)
    question = models.ForeignKey(Question, models.CASCADE, related_name="options")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.title:
            raise ValidationError(_("Title is required"))

        if not is_valid_content(self.title_uz) and not is_valid_content(self.title_ru) and not is_valid_content(
                self.title_en):
            raise ValidationError(_("Invalid content"))

        if not self.title_uz:
            self.title_uz = self.title
        if not self.title_ru:
            self.title_ru = self.title
        if not self.title_en:
            self.title_en = self.title

        if self.title_uz and self.title_ru and self.title_en:
            self.title_uz = validate_content(self.title_uz)
            self.title_ru = validate_content(self.title_ru)
            self.title_en = validate_content(self.title_en)

        super(Option, self).save(*args, **kwargs)


class UserOlimpic(BaseModel):
    user = models.ForeignKey("bot.TelegramProfile", models.CASCADE, related_name="user_olimpics")
    olimpic = models.ForeignKey(Olimpic, models.CASCADE, related_name="user_olimpics")

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    olimpic_duration = models.DurationField(null=True, blank=True)

    correct_answers = models.PositiveIntegerField(null=True, blank=True)
    wrong_answers = models.PositiveIntegerField(null=True, blank=True)
    not_answered = models.PositiveIntegerField(null=True, blank=True)

    certificate = models.FileField(upload_to="certificates", null=True, blank=True)

    def save(self, *args, **kwargs):
        return super(UserOlimpic, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.olimpic}"


class UserQuestion(BaseModel):
    olimpic = models.ForeignKey(Olimpic, models.CASCADE, related_name="user_questions")
    user = models.ForeignKey("bot.TelegramProfile", models.CASCADE, related_name="user_questions")
    question = models.ForeignKey(Question, models.CASCADE, related_name="user_questions")

    is_sent = models.BooleanField(default=False, db_index=True)
    is_answered = models.BooleanField(default=False, db_index=True)

    is_correct = models.BooleanField(default=False, db_index=True)

    message_id = models.PositiveBigIntegerField(default=0)
    content_message_id = models.PositiveBigIntegerField(default=0)
    task_id = models.CharField(max_length=255, null=True, blank=True)
    next_task_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.question}"


class UserQuestionOption(BaseModel):
    user_question = models.ForeignKey(UserQuestion, models.CASCADE, related_name="user_question_options")
    option = models.ForeignKey(Option, models.CASCADE, related_name="user_question_options")
    order = models.PositiveIntegerField(db_index=True)

    def __str__(self):
        return f"{self.user_question} - {self.option} - {self.order}"





auditlog.register(Olimpic)
auditlog.register(UserOlimpic)