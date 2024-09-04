from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from solo.admin import SingletonModelAdmin

from . import models
from common.mixins import TabbedTranslationAdmin, TranslationRequiredMixin


@admin.register(models.Region)
class RegionAdmin(ImportExportModelAdmin, TabbedTranslationAdmin):
    list_display = ("id", "title", 'parent', "created_at", "updated_at")
    list_display_links = ("id", "title", 'parent')
    list_filter = ("created_at", "updated_at")
    search_fields = ("title",'parent', )


@admin.register(models.District)
class DistrictAdmin(ImportExportModelAdmin, TabbedTranslationAdmin,TranslationRequiredMixin):
    list_display = ("id", "title", "parent", "created_at", "updated_at")
    list_display_links = ("id", "title")
    list_filter = ("parent", "created_at", "updated_at")
    search_fields = ("title", "parent")


class SchoolResource(resources.ModelResource):
    district = fields.Field(
        column_name='district_title',
        attribute='district',
        widget=ForeignKeyWidget(models.District, 'title')
    )

    class Meta:
        model = models.School
        fields = ('id', "district", "title")
        export_order = ('id', 'district','title',)

@admin.register(models.School)
class SchoolAdmin(ImportExportModelAdmin, TabbedTranslationAdmin):
    resource_class = SchoolResource
    list_display = ("id", "title", "title_uz", "title_ru", "title_en", "district",)
    list_display_links = ("id", "title")
    list_filter = ("district",)
    search_fields = ("title", "district")
