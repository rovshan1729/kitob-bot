import requests
from celery import shared_task
from tgbot.bot.utils import get_all_users
from tgbot.bot.loader import gettext as _
import environ

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
        

@shared_task
def send_daily_message():
    users = get_all_users()
    for user in users:
        try:
            send_message(chat_id=user.telegram_id, text=_("Notification"))
        except Exception as e:
            print(f"Error sending message to {user.telegram_id}: {e}")
