# Generated by Django 4.2.11 on 2024-04-27 15:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0005_settings_bot_token"),
    ]

    operations = [
        migrations.CreateModel(
            name="District",
            fields=[],
            options={
                "verbose_name": "District",
                "verbose_name_plural": "Districts",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("common.region",),
        ),
    ]
