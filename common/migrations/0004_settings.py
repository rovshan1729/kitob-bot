# Generated by Django 4.2.11 on 2024-04-22 06:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0003_remove_class_title_en_remove_class_title_ru_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Settings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "site_name",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Site name"
                    ),
                ),
                (
                    "site_logo",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="uploads/%Y/%m/%d/",
                        verbose_name="Site logo",
                    ),
                ),
                (
                    "host_url",
                    models.URLField(blank=True, null=True, verbose_name="Host URL"),
                ),
            ],
            options={
                "verbose_name": "Settings",
            },
        ),
    ]
