from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from telegram import Bot

from bot.models import Notification
from bot import tasks
from django.utils import timezone

@receiver(post_save, sender=Notification)
def send_notification(sender, instance, created, **kwargs):
    if created:
        tasks.send_notification.apply_async(args=(instance.id,), eta=timezone.now() + timezone.timedelta(seconds=5))
        return instance