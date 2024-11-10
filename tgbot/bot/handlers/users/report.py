import asyncio
from aiogram import types
from aiogram.dispatcher import FSMContext

from tgbot.models import BookReport, ReportMessage, LastTopicID, ConfirmationReport
from tgbot.bot.keyboards.reply import confirm_markup, main_markup, back_keyboard
from tgbot.bot.loader import dp, bot
from tgbot.bot.loader import gettext as _
from tgbot.bot.states.main import ReportState
from tgbot.bot.utils import get_user
from aiogram.dispatcher.filters.builtin import ChatTypeFilter
from aiogram.types import ChatType

from datetime import datetime
from django.utils import timezone


@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), text="📚 Kitob hisoboti", state="*")
@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), text="📚 Отчет о книге", state="*")
async def send_daily_report_handler(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user.is_blocked:
        await message.answer(_("Siz bot tomonidan bloklangansiz."))
        return await state.finish()

    await message.answer(_("Nechanchi kun o'qiyotganingizni kiriting:"), reply_markup=back_keyboard)
    await ReportState.reading_day.set()
    
    
@dp.message_handler(state=ReportState.reading_day)
async def process_reading_day(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    language = user.language
    
    if message.text == _("🔙 Orqaga"):
        await message.answer(_("Bosh menyu"), reply_markup=main_markup(language=language))
        await state.finish()
        return 
    
    day = message.text
    if not day.isdigit():
        await message.answer(_("Iltimos, to'g'ri kun raqamini kiriting."), reply_markup=back_keyboard)
        return

    if 1 > int(day) or int(day) > 500:
        await message.answer(_("Iltimos, to'g'ri kun raqamini kiriting."), reply_markup=back_keyboard)
        return
    
    await state.update_data(reading_day=int(day))
    await message.answer(_("Qaysi kitobni o'qiyotganingizni kiriting:"), reply_markup=back_keyboard)
    await ReportState.book_title.set()
    
    
@dp.message_handler(state=ReportState.book_title)
async def process_book_title(message: types.Message, state: FSMContext):
    if message.text == _("🔙 Orqaga"):
        await message.answer(_("Nechanchi kun o'qiyotganingizni kiriting:"), reply_markup=back_keyboard)
        return await ReportState.reading_day.set()
    
    book_title = message.text.strip()
    is_correct = message.text.split(' ')
    
    if len(is_correct) < 1 or len(is_correct) > 10:
        await message.answer(_("Iltimos, kitobni nomini to'g'ri kiriting!"))
        return
    
    if len(book_title) > 120:
        await message.answer(_("Iltimos, kitobni nomi uzun bo'lmasin!"))
        return
        
    await state.update_data(book_title=book_title)
    await message.answer(_("Nechi bet o'qiganingizni kiriting:"), reply_markup=back_keyboard)
    await ReportState.pages_read.set()
    

@dp.message_handler(state=ReportState.pages_read)
async def process_pages_read(message: types.Message, state: FSMContext):
    if message.text == _("🔙 Orqaga"):
        await message.answer(_("Qaysi kitobni o'qiyotganingizni kiriting:"), reply_markup=back_keyboard)
        return await ReportState.book_title.set()

    user = get_user(message.from_user.id)
    language = user.language
    pages_read = message.text
    if not pages_read.isdigit():
        await message.answer(_("Iltimos, to'g'ri bet raqamini kiriting."), reply_markup=back_keyboard)
        return
    
    if 1 > int(pages_read) or int(pages_read) > 300:
        await message.answer(_("Iltimos, nechi bet o'qiganingizni raqamini to'g'ri kiriting."), reply_markup=back_keyboard)
        return
    
    await state.update_data(pages_read=int(pages_read))

    today = datetime.now()
    
    data = await state.get_data()
    confirmation_message = (
        f"@{user.username}\n\n"
        f"<b>{user.full_name}</b>\n\n📊#kun - {data['reading_day']}  ({today.date()})\n\n"
        f"<b>Kitob nomi:</b> {data['book_title']}\n\n"
        f"<b>✅O‘qilgan betlar:</b> {pages_read}+ bet\n\n"
        "Tasdiqlaysizmi?"
    )

    await message.answer(confirmation_message, reply_markup=confirm_markup(language=language), parse_mode='HTML')
    await ReportState.confirm_report.set()

    await asyncio.sleep(5*60)
    current_state = await state.get_state()

    if current_state == ReportState.confirm_report.state:
        await message.answer("Tasqidlaysizmi?", reply_markup=confirm_markup(language=language), parse_mode='HTML')


last_report_message = None
last_report_date = None
counter = 0

@dp.message_handler(state=ReportState.confirm_report)
async def confirm_report(message: types.Message, state: FSMContext):
    global last_report_message, last_report_date, counter

    user = get_user(message.from_user.id)
    language = user.language

    if message.text.lower() != _("tasdiqlash"):
        await message.answer(_("Bekor qilindi."), reply_markup=main_markup(language=language))
        await state.finish()

    today = timezone.now().date()

    # existing_report = BookReport.objects.filter(user=user, created_at__date=today).exists()
    #
    # if existing_report:
    #     await message.answer(_("Siz bugungi kun uchun allaqachon hisobotingizni yubordingiz."), reply_markup=main_markup(language=language))
    #     await state.finish()
    #     return

    data = await state.get_data()
    reading_day = data.get("reading_day")
    book = data.get("book_title")
    pages_read = data.get("pages_read")

    book_report = BookReport.objects.filter(user=user).first()

    if book_report:
        book_report.book = book
        book_report.reading_day = reading_day
        book_report.pages_read = pages_read
        book_report.save()
    else:
        BookReport.objects.create(
            user=user,
            reading_day=reading_day,
            book=book,
            pages_read=pages_read,
        )
    datetime_now = timezone.now()
    ConfirmationReport.objects.create(
        user=user,
        pages_read=pages_read,
        date=datetime_now,
        book=book
    )
    await message.answer(_("Hisobotingiz yuborildi."), reply_markup=main_markup(language=language))
    last_date = ConfirmationReport.objects.filter(user=user).order_by('-date').first()

    new_report_message = (
        f"@{user.username}\n\n"
        f"<b>{user.full_name}</b>\n\n📊#kun - {reading_day}  ({last_date.date.strftime('%Y-%m-%d')})\n\n"
        f"<b>Kitob nomi:</b> {book}\n\n"
        f"<b>✅O‘qilgan betlar:</b> {pages_read}+ bet\n\n"
        f"<i>----------------------------------</i>"
    )

    if user.group:
        chat_id = user.group.chat_id
        topic_id = user.group.topic_id
    else:
        chat_id = "-1002237773868"
        topic_id = 3336

    last_topic_instance = LastTopicID.get_solo()
    group = user.group

    report_message, created = ReportMessage.objects.get_or_create(
        chat_id=chat_id,
        last_update=today,
        group=group,
        defaults={'message_count': 0, 'message_text': '', 'message_id': None, 'group': group}
    )

    if report_message.last_update != today:
        new_message = await bot.send_message(
            chat_id=chat_id,
            message_thread_id=topic_id,
            text=new_report_message,
            parse_mode='HTML'
        )

        report_message.message_id = new_message.message_id
        report_message.topic_id = new_message.topic_id
        report_message.message_text = new_report_message
        report_message.message_count = 1
        report_message.last_update = today
        report_message.save()

    else:
        try:
            updated_message_text = report_message.message_text + f"\n\n{new_report_message}"

            if int(last_topic_instance.topic_id) == int(topic_id):
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=report_message.message_id,
                    text=updated_message_text,
                    parse_mode='HTML'
                )

                report_message.message_text = updated_message_text
                report_message.message_count += 1
                report_message.save()

            else:
                new_message = await bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=topic_id,
                    text=new_report_message,
                    parse_mode='HTML'
                )

                report_message.message_id = new_message.message_id
                report_message.topic_id = topic_id
                report_message.message_text = new_report_message
                report_message.message_count = 1
                report_message.last_update = today
                report_message.save()

                last_topic_instance.topic_id = topic_id
                last_topic_instance.save()

        except Exception as e:
            last_report_message = await bot.send_message(
                chat_id=chat_id,
                message_thread_id=topic_id,
                text=new_report_message,
                parse_mode='HTML'
            )

            report_message.message_id = last_report_message.message_id
            report_message.message_text = new_report_message
            report_message.message_count = 1
            report_message.save()

            last_topic_instance.topic_id = topic_id
            last_topic_instance.save()

    await state.finish()
