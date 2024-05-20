import time
from django.core.management.base import BaseCommand

from bot.models import TelegramProfile as User
from utils.bot import send_message


class Command(BaseCommand):
    help = 'Send Notifications'

    def handle(self, *args, **options):
        text = ("Kelajak yoshlari Olimpiadasi bugun 23:59 gacha ochiq! Agar siz haliham test yechmagan bo'lsangiz, "
                "/start ni bosing va 🏆Olimpiadalar🏆 bo'limidan test topshiring va sovg'alaringizni yutib oling! "
                "Murojaat: @roboteachhelp")
        success_count = failed_count = 0
        users = User.objects.filter(class_room__in=["5-sinf", "6-sinf", "7-sinf"])
        self.stdout.write(self.style.SUCCESS("Xabar yuborish boshlandi"))
        for user in users:
            response = send_message(chat_id=user.telegram_id, text=text)
            if response.status_code == 200:
                success_count += 1
            else:
                failed_count += 1
            time.sleep(0.05)
        self.stdout.write(self.style.SUCCESS(f"Muvaffaqiyatli yuborilganlar: {success_count} ta\n\nYubora olmaganlar: {failed_count} ta"))
