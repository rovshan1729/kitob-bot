# Generated by Django 4.2.11 on 2024-05-19 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bot", "0018_alter_telegramprofile_is_registered"),
    ]

    operations = [
        migrations.AddField(
            model_name="telegrambutton",
            name="file_id",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="File ID"
            ),
        ),
    ]
