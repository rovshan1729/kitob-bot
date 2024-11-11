import random
import requests
from celery import shared_task
from django.db.models.functions.window import Rank
from django.utils.timezone import now

from tgbot.bot.utils import get_all_users
import environ
from tgbot.models import DailyMessage, BookReport, BlockedUser, \
    Group, ConfirmationReport, TelegramProfile
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Q, Window, F

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
    today_end = today_start + timedelta(days=1)
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

                if status != 200:
                    BlockedUser.objects.get_or_create(user=user)
                    send_message(chat_id=631751797, text=f'Blocked User {user.full_name} - {user.username}')

    send_message(chat_id=631751797, text=f"Users reported: {users_reported}\n"
                                         f"Users not reported: {users_not_reported}")


@shared_task
def daily_top_read_user():
    send_message(631751797, "daily_works")
    today = now().date()
    # top_users = ConfirmationReport.objects.filter(date__date=today) \
    #     .annotate(total_pages=Sum('pages_read')) \
    #     .order_by('-total_pages').distinct('user')[:10]

    ranked_reports = ConfirmationReport.objects.filter(date__date=today).annotate(
        total_pages=Sum('pages_read'),
        rank=Window(
            expression=Rank(),
            partition_by=F('user_id'),
            order_by=F('total_pages').desc()
        )
    ).filter(rank=1).order_by('-total_pages')[:10]

    if ranked_reports:
        message = f"📚 Bugun eng ko'p kitob o'qigan 10ta Peshqadam foydalanuvchilar: \n\n"
        for index, user in enumerate(ranked_reports, start=1):
            message += f"{index}) @{user.user.username} <b>{user.user.full_name}</b>: {user.pages_read} bet 📚\n\n"
    else:
        message = "📚 Kecha uchun kitob o'qigan foydalanuvchilar yo'q."

    group_instance = Group.objects.first()
    chat_id = group_instance.chat_id
    send_message(chat_id, message)



@shared_task
def weekly_top_read_user():
    send_message(631751797, "weekly_works")
    send_message(6956376313, "weekly_works")

    weekly_start_date = timezone.now() - timedelta(days=7)

    weekly = now() - timedelta(days=7)
    # top_users = ConfirmationReport.objects.filter(
    #     Q(date__date__gte=weekly.date()) &
    #     Q(date__date__lte=now().date())
    #     ).annotate(
    #     total_pages=Sum('pages_read')
    # ).order_by('-total_pages')[:10]

    weekly_ranked_reports = ConfirmationReport.objects.filter(Q(date__date__gte=weekly.date()) &
        Q(date__date__lte=now().date())).annotate(
        total_pages=Sum('pages_read'),
        rank=Window(
            expression=Rank(),
            partition_by=F('user_id'),
            order_by=F('total_pages').desc()
        )
    ).filter(rank=1).order_by('-total_pages')[:10]

    if weekly_ranked_reports:
        message = f"📚 Bu hafta eng ko'p kitob o'qigan 10ta Peshqadam foydalanuvchilar: \n"
        for index, user in enumerate(weekly_ranked_reports, start=1):
            message += f"{index}) @{user.user.username} <b>{user.user.full_name}</b>: {user.pages_read} bet 📚\n\n"
    else:
        message = "📚 Bu hafta uchun kitob o'qigan foydalanuvchilar yo'q."

    group_instance = Group.objects.first()
    chat_id = group_instance.chat_id
    send_message(chat_id, message)


@shared_task
def monthly_top_read_user():
    send_message(631751797, "monthly_works")
    send_message(6956376313, "monthly_works")

    monthly_start_date = timezone.now() - timedelta(days=30)

    monthly = now() - timedelta(days=30)
    top_users = ConfirmationReport.objects.filter(
        Q(date__date__gte=monthly.date()) &
        Q(date__date__lte=now().date())
        ).annotate(
        total_pages=Sum('pages_read')
    ).order_by('-total_pages')[:15]

    if top_users:
        message = f"📚 Bu oy eng ko'p kitob o'qigan 15ta Peshqadam foydalanuvchilar: \n"
        for index, user in enumerate(top_users, start=1):
            message += f"{index}) @{user['user__username']} <b>{user['user__full_name']}</b>: {user['total_pages']} bet 📚\n\n"
    else:
        message = "📚 Bu oy uchun kitob o'qigan foydalanuvchilar yo'q."

    group_instance = Group.objects.first()
    chat_id = group_instance.chat_id
    send_message(chat_id, message)


@shared_task
def yearly_top_read_user():
    send_message(631751797, "yearly_works")
    send_message(6956376313, "yearly_works")

    yearly_start_date = timezone.now() - timedelta(days=365)

    top_users = ConfirmationReport.objects.filter(
        Q(date__date__gte=yearly.date()) & Q(date__date__lte=now().date())
        ).annotate(
        total_pages=Sum('pages_read')
    ).order_by('-total_pages')[:30]

    if top_users:
        message = f"📚 Bu yil eng ko'p kitob o'qigan 30 ta Peshqadam foydalanuvchilar: \n\n"
        for index, user in enumerate(top_users, start=1):
            message += f"{index}) @{user['user__username']} <b>{user['user__full_name']}</b>: {user['total_pages']} bet 📚\n\n"
    else:
        message = "📚 Bu yil uchun kitob o'qigan foydalanuvchilar yo'q."

    group_instance = Group.objects.first()
    chat_id = group_instance.chat_id
    send_message(chat_id, message)


@shared_task
def users_unread_book():
    today = timezone.now()
    users = TelegramProfile.objects.exclude(confirmationreport__date=today.date())

    if users:
        users_count = users.count()
        message = f"‼️ Bugun hisobot yubormaganlar: {users_count}ta\n\n"
        for user in users:
            if user.full_name is None:
                user.delete()
            else:
                if user.telegram_id != 631751797:
                    message += f"-@{user.username} (<b>{user.full_name}</b>)\n"

        message += "\nKuniga 5-10 daqiqa va siz yana safdasiz 🚀 \n\n *Bizdan qolib ketmysiz degan umiddamiz xurmatli do‘stlar"
        group_instance = Group.objects.first()
        chat_id = group_instance.chat_id
        send_message(chat_id, message)

