import random

import requests
from celery import shared_task
from tgbot.bot.utils import get_all_users
import environ
from tgbot.models import DailyMessage, BookReport, BlockedUser
from django.utils import timezone

env = environ.Env()


BOT_TOKEN = env.str("API_TOKEN")

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
    response = requests.post(url, data=data)
    return response.json(), response.status_code


@shared_task(acks_late=True)
def send_daily_message():
    users = get_all_users().only('telegram_id', 'id')

    today_start = timezone.now().date()
    today_end = today_start + timezone.timedelta(days=1)
    reported_users = set(
        BookReport.objects.filter(created_at__range=(today_start, today_end)).values_list('user_id', flat=True)
    )

    users_reported = 0
    users_not_reported = 0

    for user in users:
        users_reported += 1
        if user.id not in reported_users:
            users_not_reported += 1
            unsent_messages = DailyMessage.objects.all()
            if unsent_messages.exists():
                message_instance = random.choice(unsent_messages)
                message_text = message_instance.message
                response, status = send_message(chat_id=user.telegram_id, text=message_text)

                if status == 400:
                    BlockedUser.objects.get_or_create(user=user)
                    send_message(chat_id=631751797,text=f'Blocked User {user.full_name}, {user.username}')


    send_message(chat_id=631751797, text=f"Users reported: {users_reported}\n"
                                         f"Users not reported: {users_not_reported}")