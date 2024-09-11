from aiogram import types
from aiogram.dispatcher import FSMContext

from tgbot.models import BookReport
from tgbot.bot.keyboards.reply import confirm_markup, main_markup, back_keyboard
from tgbot.bot.loader import dp, bot
from tgbot.bot.loader import gettext as _
from tgbot.bot.states.main import ReportState
from tgbot.bot.utils import get_user



@dp.message_handler(text=_("Book report"), state="*")
async def send_daily_report_handler(message: types.Message, state: FSMContext):
    await message.answer(_("Nechanchi kun o'qiyotganingizni kiriting:"), reply_markup=back_keyboard)
    await ReportState.enter_reading_day.set()
    
    
@dp.message_handler(state=ReportState.enter_reading_day)
async def process_reading_day(message: types.Message, state: FSMContext):
    if message.text == _("🔙 Orqaga"):
        await message.answer(_("Bosh menyu"), reply_markup=main_markup(language=language))
        await state.finish()
        return 
    
    user = get_user(message.from_user.id)
    language = user.language
    
    day = message.text
    if not day.isdigit():
        await message.answer(_("Iltimos, to'g'ri kun raqamini kiriting."), reply_markup=back_keyboard)
        return

    if 1 <= int(day) <= 1000:
        await message.answer(_("Iltimos, to'g'ri kun raqamini kiriting."), reply_markup=back_keyboard)
        return
    
    await state.update_data(reading_day=int(day))
    await message.answer(_("Qaysi kitobni o'qiyotganingizni kiriting:"), reply_markup=back_keyboard)
    await ReportState.enter_book_title.set()
    
    
@dp.message_handler(state=ReportState.enter_book_title)
async def process_book_title(message: types.Message, state: FSMContext):
    if message.text == _("🔙 Orqaga"):
        await message.answer(_("Nechanchi kun o'qiyotganingizni kiriting:"), reply_markup=back_keyboard)
        return await ReportState.enter_reading_day.set()
    
    book_title = message.text.strip()
    is_correct = message.text.split(' ')
    
    if len(is_correct) <= 1 or len(is_correct) > 10:
        await message.answer(_("Iltimos, kitobni nomini to'g'ri kiriting."))
        return
    
    if len(book_title) > 60:
        await message.answer(_("Iltimos, kitobni nomini to'g'ri kiriting"))
        return
        
    await state.update_data(book_title=book_title)
    await message.answer(_("Nechi bet o'qiganingizni kiriting:"), reply_markup=back_keyboard)
    await ReportState.enter_pages_read.set()
    

@dp.message_handler(state=ReportState.enter_pages_read)
async def process_pages_read(message: types.Message, state: FSMContext):
    pages = message.text
    if not pages.isdigit():
        await message.answer(_("Iltimos, to'g'ri bet raqamini kiriting."), reply_markup=back_keyboard)
        return
    
    if 1 <= int(pages) <= 2000:
        await message.answer(_("Iltimos, nechi bet o'qiganingizni raqamini to'g'ri kiriting."), reply_markup=back_keyboard)
        return
    
    await state.update_data(pages_read=int(pages))
    
    data = await state.get_data()
    confirmation_message = (
        f"{data['reading_day']}-kun\n {data['book_title']}.\n {data['pages_read']}+ bet.\n"
        "Tasdiqlaysizmi?"
    )
    
    await message.answer(confirmation_message, reply_markup=confirm_markup())
    await ReportState.confirm_report.set()


@dp.message_handler(state=ReportState.confirm_report)
async def confirm_report(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    language = user.language

    if message.text.lower() != _("tasdiqlash"):
        await message.answer(_("Bekor qilindi."), reply_markup=main_markup(language=language))
        await state.finish()

    data = await state.get_data()
    
    reading_day = data.get("reading_day")
    book = data.get("book_title")
    pages_read = data.get("pages_read")
        
    BookReport.objects.create(
        user=user,
        reading_day=reading_day,
        book=book,
        pages_read=pages_read
    )
    
    await message.answer(_("Hisobotingiz yuborildi."), reply_markup=main_markup())
    
    report_message = (
        f"@{user.username}\n {data['reading_day']}-kun\n {data['book_title']}.\n {data['pages_read']}+ bet."
    )
    await bot.send_message(chat_id="-4507787012", text=report_message)
    
    await state.finish()
