# Generated by Django 4.2.11 on 2024-04-20 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("olimpic", "0011_userquestion_content_message_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userolimpic",
            name="start_time",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
