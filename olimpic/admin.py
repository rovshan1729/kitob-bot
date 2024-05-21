from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export import resources, fields, widgets
from import_export.admin import ImportExportModelAdmin
from django import forms
from PIL import Image

from common.mixins import TabbedTranslationAdmin, TranslationRequiredMixin
from olimpic import models

# Register your models here.


admin.site.register(models.UserQuestion)
admin.site.register(models.UserQuestionOption)
# admin.site.register(models.UserOlimpic)
# admin.site.register(models.OlimpicCertifeicate)


class UserOlimpicResource(resources.ModelResource):
    def __init__(self, *args, **kwargs):
        super(UserOlimpicResource, self).__init__(*args, **kwargs)
        self.fields['user__full_name'].column_name = _('Full Name')
        self.fields['olimpic__title'].column_name = _('Olimpic')
        self.fields['start_time'].column_name = _('Start Time')
        self.fields['end_time'].column_name = _('End Time')
        self.fields['correct_answers'].column_name = _('Correct Answers')
        self.fields['wrong_answers'].column_name = _('Wrong Answers')
        self.fields['not_answered'].column_name = _('Not Answered')

    class Meta:
        model = models.UserOlimpic
        fields = ('id', 'user__full_name', 'olimpic__title', 'start_time', 'end_time', 'correct_answers', 'wrong_answers', 'not_answered')
        export_order = ('id', 'user__full_name', 'olimpic__title', 'start_time', 'end_time', 'correct_answers', 'wrong_answers', 'not_answered')



@admin.register(models.UserOlimpic)
class UserOlimpicAdmin(ImportExportModelAdmin, TabbedTranslationAdmin):
    resource_class = UserOlimpicResource
    list_display = ('id', 'olimpic', 'user', 'olimpic_duration', 'correct_answers', 'wrong_answers', 'not_answered')
    list_display_links = ('id', 'olimpic', 'user')
    search_fields = ('olimpic__title', 'user__full_name')
    list_filter = ('olimpic', 'user')
    ordering = ('-correct_answers', 'olimpic_duration', 'wrong_answers', 'not_answered', 'id',)


class QuestionInline(admin.StackedInline):
    model = models.Question
    extra = 1

class OlimpicCertificateFormset(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False  # Disallow empty forms

    # def clean(self):
    #     super().clean()
    #     for form in self.forms:
    #         if not form.cleaned_data.get('certificate'):
    #             form.add_error('certificate', _('This field is required.'))
    #         image = Image.open(form.cleaned_data.get('certificate'))
    #         if image.width != 1582 and image.height != 1172:
    #             form.add_error('certificate', _('Image size must be 1582x1172.'))


class OlimpicCertifeicateInline(admin.TabularInline):
    model = models.OlimpicCertifeicate
    extra = 1
    formset = OlimpicCertificateFormset


@admin.register(models.Olimpic)
class OlimpicAdmin(TranslationRequiredMixin, TabbedTranslationAdmin):
    list_display = ("id","title",'start_time','end_time', "is_active")
    list_display_links = ("id","title",)
    search_fields = ("title",)
    inlines = [OlimpicCertifeicateInline]



class OptionInlineFormset(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False  # Disallow empty forms

    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.cleaned_data.get('title'):
                form.add_error('title', _('This field is required.'))

class OptionInline(admin.TabularInline):
    model = models.Option
    extra = 0
    formset = OptionInlineFormset


class QuestionResource(resources.ModelResource):
    def __init__(self, *args, **kwargs):
        super(QuestionResource, self).__init__(*args, **kwargs)
        self.fields['text'].column_name = _('Text')
        self.fields['olimpic__title'].column_name = _('Olimpic')
        self.fields['duration'].column_name = _('Duration')

    # def import_row(
    #     self,
    #     row,
    #     instance_loader,
    #     using_transactions=True,
    #     dry_run=False,
    #     raise_errors=None,
    #     **kwargs
    # ):
    #     print("ROW")
    #     print(row)
    #     print("ROW")
    #     return super().import_row(row, instance_loader, using_transactions, dry_run, raise_errors, **kwargs)
    #
    # def import_obj(self, obj, data, dry_run, **kwargs):
    #     print("OBJ")
    #     print(obj)
    #     print("OBJ")
    #     return super().import_obj(obj, data, dry_run, **kwargs)

    def import_field(self, field, obj, data, is_m2m=False, **kwargs):
        print("FIELD")
        print(field, obj, data)
        print("FIELD")

        return super().import_field(field, obj, data, is_m2m, **kwargs)

    # def import_data(
    #     self,
    #     dataset,
    #     *args,
    #     **kwargs
    # ):
    #     print("DATASET")
    #     print(dataset)
    #     print("DATASET")
    #     return super().import_data(dataset, *args, **kwargs)

    class Meta:
        model = models.Question
        fields = ('id', 'text', 'olimpic__title', 'duration')
        export_order = ('id', 'text', 'olimpic__title', 'duration')


@admin.register(models.Question)
class QuestionAdmin(ImportExportModelAdmin, TranslationRequiredMixin, TabbedTranslationAdmin):
    resource_class = QuestionResource
    list_display = ("id","text","olimpic", "duration")
    list_display_links = ("id","text",)
    search_fields = ("text",'olimpic__title')
    list_filter = ("olimpic",)

    inlines = [OptionInline]


# @admin.register(models.Option)
# class OptionAdmin(TranslationRequiredMixin, TabbedTranslationAdmin):
#     list_display = ("id","title",)
#     list_display_links = ("id","title",)
#     search_fields = ("title",)
#     list_filter = ("question",)