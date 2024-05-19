# Generated by Django 4.2.11 on 2024-04-16 06:39

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bot", "0004_requiredgroup_title_en_requiredgroup_title_ru_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="telegrambutton",
            name="text",
            field=ckeditor.fields.RichTextField(verbose_name="Button Text"),
        ),
        migrations.AlterField(
            model_name="telegrambutton",
            name="text_en",
            field=ckeditor.fields.RichTextField(null=True, verbose_name="Button Text"),
        ),
        migrations.AlterField(
            model_name="telegrambutton",
            name="text_ru",
            field=ckeditor.fields.RichTextField(null=True, verbose_name="Button Text"),
        ),
        migrations.AlterField(
            model_name="telegrambutton",
            name="text_uz",
            field=ckeditor.fields.RichTextField(null=True, verbose_name="Button Text"),
        ),
    ]
