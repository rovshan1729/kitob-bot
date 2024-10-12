import requests
from celery import shared_task
from tgbot.bot.utils import get_all_users
import environ
from tgbot.models import DailyMessage, BookReport
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

    daily_message = DailyMessage.load()
    message_text = daily_message.message

    now = timezone.now()

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
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
            response, status = send_message(chat_id=user.telegram_id, text=message_text)
            send_message(chat_id=631751797, text=f"notification sent to {user.full_name}\n"
                                                 f"Response {response}\n"
                                                 f"Status {status}\n"
                                                 f"Time {now}")

    send_message(chat_id=631751797, text=f"Users reported: {users_reported}\n"
                                         f"Users not reported: {users_not_reported}")