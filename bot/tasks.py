import time
import requests
from src.celery_app import app as celery_app
from django.conf import settings
from django.utils import timezone

from .models import Notification, TelegramProfile, UserNotification

def send_notif(chat_id, text, **kwargs):
    params = {
        'chat_id': chat_id,
        'parse_mode': 'HTML',
    }
    content = kwargs.get('content', None)
    action = kwargs.get('action', None)
    if action == "audio" and content:
        method = 'sendAudio'
        params['audio'] = content
        params['caption'] = text
    elif action == "photo" and content:
        method = 'sendPhoto'
        params['photo'] = content
        params['caption'] = text
    elif action == "video" and content:
        method = 'sendVideo'
        params['video'] = content
        params['caption'] = text
    elif action == "document" and content:
        method = 'sendDocument'
        params['document'] = content
        params['caption'] = text
    else:
        method = 'sendMessage'
        params['text'] = text

    url = f'https://api.telegram.org/bot{settings.API_TOKEN}/{method}'

    response = requests.post(url, params=params)
    return response, params


@celery_app.task
def send_notification(notification_id):
    notification = Notification.objects.filter(id=notification_id).first()
    while not notification:
        notification = Notification.objects.filter(id=notification_id).first()
        if notification:
            return

    users_query = TelegramProfile.objects.all()

    if notification.is_all_users:
        profiles = users_query.all()
    elif notification.is_not_registered:
        profiles = users_query.filter(is_registered=False)
    elif notification.region:
        profiles = users_query.filter(region_id=notification.region_id)
    elif notification.district:
        profiles = users_query.filter(district=notification.district)
    elif notification.school:
        profiles = users_query.filter(school=notification.school)
    elif notification.class_room:
        profiles = users_query.filter(class_room=notification.class_room)
    elif notification.users:
        profiles = notification.users.all()
    else:
        profiles = None


    for profile in profiles:
        user_notification = UserNotification.objects.create(user=profile,notification=notification,)
        action = None
        content = None
        text = f"<b>{getattr(notification, f'title_{profile.language}')}</b>\n\n{getattr(notification, f'text_{profile.language}')}"
        if notification.file_content and notification.file_content.name.split('.')[-1] in ['jpg', 'jpeg', 'png']:
            action = "photo"
            content = settings.BACK_END_URL + notification.file_content.url
        elif notification.file_content and notification.file_content.name.split('.')[-1] in ['mp4',]:
            action = "video"
            content = settings.BACK_END_URL + notification.file_content.url
        elif notification.file_content and notification.file_content.name.split('.')[-1] in ['mp3', "wav"]:
            action = "audio"
            content = settings.BACK_END_URL + notification.file_content.url
        elif notification.file_content and notification.file_content.name.split('.')[-1] in ['pdf', "docx", "doc", "xls", "xlsx"]:
            action = "document"
            content = settings.BACK_END_URL + notification.file_content.url


        response, params = send_notif(profile.telegram_id, text, action=action, content=content)
        user_notification.is_sent = response.status_code == 200
        user_notification.sent_at = timezone.now()
        user_notification.request_body = params
        user_notification.response_body = response.json()

        if not response.status_code == 200:
            user_notification.error_message = response.text

        user_notification.save()
        time.sleep(0.05)

    notification.sent_count = UserNotification.objects.filter(notification=notification, is_sent=True).count()
    notification.fail_count = UserNotification.objects.filter(notification=notification, is_sent=False).count()
    notification.save()