import io
from src.celery_app import app as celery_app
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from urllib.request import urlopen

from olimpic.models import UserOlimpic, Olimpic

from docxtpl import DocxTemplate


@celery_app.task
def generate_certificates(user_olimpic_id):
    user_olimpic = UserOlimpic.objects.get(id=user_olimpic_id)
    olimpic = Olimpic.objects.get(id=user_olimpic.olimpic_id)

    if not olimpic.certificate:
        return "Stopped"

    font = "static/assets/font.ttf"

    user_olimpics = UserOlimpic.objects.filter(
        olimpic=olimpic,
        correct_answers__isnull=False,
        wrong_answers__isnull=False,
        # not_answered__isnull=False,
        olimpic_duration__isnull=False,
    ).order_by("-correct_answers", "wrong_answers", "not_answered", "olimpic_duration").select_related("user")

    im = Image.open(olimpic.certificate.certificate)

    if im.width != 1582 and im.height != 1172:
        return "Stopped"



    full_name_font = ImageFont.truetype(font, size=38)
    full_name = user_olimpic.user.full_name
    draw = ImageDraw.Draw(im)
    draw.text((600, 480), full_name, fill="indigo", font=full_name_font)

    main_font = ImageFont.truetype(font, size=23)
    olimpic_date = user_olimpic.start_time.date().strftime('%d.%m.%Y')
    draw.text((635, 1065), olimpic_date, fill="indigo", font=main_font)

    correct = str(user_olimpic.correct_answers)
    draw.text((840, 1065), correct, fill="indigo", font=main_font)

    olimpic_place = str(list(user_olimpics).index(user_olimpic) + 1)
    draw.text((1025, 1065), olimpic_place, fill="indigo", font=main_font)

    qrcode = Image.open("static/assets/qrcode.png")
    new_qrcode = qrcode.resize((130, 130))
    im.paste(new_qrcode, (1340, 970))
    buffer = io.BytesIO()
    im.save(buffer, format='JPEG')
    user_olimpic.certificate.save(f'{user_olimpic.user.username}.jpeg', ContentFile(buffer.getvalue()))
