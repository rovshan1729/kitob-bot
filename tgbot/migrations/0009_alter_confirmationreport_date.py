# Generated by Django 4.2.16 on 2024-11-10 16:56

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("tgbot", "0008_telegramprofile_is_admin"),
    ]

    operations = [
        migrations.AlterField(
            model_name="confirmationreport",
            name="date",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
