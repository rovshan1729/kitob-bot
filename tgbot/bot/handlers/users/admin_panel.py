from aiogram.utils.markdown import hlink
from tgbot.bot.keyboards.reply import admin_keyboard
from aiogram.dispatcher.filters import Text
from tgbot.bot import dp
from tgbot.models import TelegramProfile, BookReport
from aiogram import types
from aiogram.dispatcher import FSMContext
from tgbot.bot.states.main import StatisticState


@dp.message_handler(commands=["admin"])
async def admin_commands(message: types.Message):
    telegram_id = message.from_user.id
    try:
        user = await TelegramProfile.objects.aget(telegram_id=telegram_id)
        if user.is_admin:
            await message.answer("Menudan birini tanlang:", reply_markup=admin_keyboard)
        else:
            await message.answer("Siz admin emassiz!")
    except TelegramProfile.DoesNotExist:
        await message.answer("Profilingiz topilmadi!")


@dp.message_handler(Text("✅ Ro'yhatdan o'tganlar"))
async def registered_lists(message: types.Message):
    reg_users = TelegramProfile.objects.filter(is_registered=True).order_by('id')
    reg_users_count = reg_users.count()

    response = f"Ro'yhatdan o'tgan userlar soni: {reg_users_count}\n"
    response += "-----------------------------------------------\n"
    response += "ID  |  User\n"
    response += "-----------------------------------------------\n"

    for user in reg_users:
        user_id = user.telegram_id
        if user.full_name:
            mention = hlink(user.full_name, f"tg://user?id={user_id}")
        else:
            mention = "Ism qo'ymagan"
        response += f"{user.id}  |  {mention}\n"

    await message.answer(response, parse_mode="HTML")


@dp.message_handler(Text("❌ Ro'yhatdan o'tmaganlar"))
async def unregistered_lists(message: types.Message):
    unreg_users = TelegramProfile.objects.filter(is_registered=False).order_by('id')
    unreg_users_count = unreg_users.count()

    response = f"Ro'yhatdan o'tmagan userlar soni: {unreg_users_count}\n"
    response += "-----------------------------------------------\n"
    response += "ID  |  User\n"
    response += "-----------------------------------------------\n"

    for user in unreg_users:
        user_id = user.telegram_id
        print(user_id)
        if user.full_name:
            mention = hlink(user.full_name, f"tg://user?id={user_id}")
        elif user.username:
            mention = hlink("@" + user.username, f"tg://user?id={user_id}")
        else:
            mention = hlink("Ism qo'yilmagan", f"tg://user?id={user_id}")

        response += f"{user.id}  |  {mention}\n"

    await message.answer(response, parse_mode="HTML")


@dp.message_handler(Text(contains="‍👩‍👦‍👦 Barcha foydalanuvchilar"))
async def all_users(message: types.Message):
    all_users = TelegramProfile.objects.all().order_by('id')
    total_users_count = all_users.count()

    response = f"Barcha foydalanuvchilar soni: {total_users_count}\n"
    response += "-----------------------------------------------\n"
    response += "ID  |  User (✅/🚫)\n"
    response += "-----------------------------------------------\n"

    for user in all_users:
        user_id = user.telegram_id

        if user.full_name:
            mention = hlink(user.full_name, f"tg://user?id={user_id}")
        elif user.username:
            mention = hlink("@" + user.username, f"tg://user?id={user_id}")
        else:
            mention = hlink("Ism qo'yilmagan", f"tg://user?id={user_id}")

        if user.is_registered:
            response += f"{user.id}  |  {mention} ✅\n"
        else:
            response += f"{user.id}  |  {mention} 🚫\n"
    await message.answer(response, parse_mode="HTML")


@dp.message_handler(Text("📊 Statistikani ko'rish"))
async def get_book_info_start(message: types.Message):
    await message.answer("Iltimos, foydalanuvchi ID'sini kiriting:", reply_markup=types.ReplyKeyboardRemove())
    await StatisticState.input_user_id.set()


@dp.message_handler(state=StatisticState.input_user_id)
async def input_user_id(message: types.Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqatgina foydalanuvchi ID'sini kiriting:")
        await StatisticState.input_user_id.set()
        return
    user_id = message.text.strip()

    try:
        user = TelegramProfile.objects.get(id=user_id)
        user_topic_id = user.group.title if user.group else None
        user_tg_id = user.telegram_id
        book_report = BookReport.objects.filter(user=user).first()

        if book_report:
            touch_user = hlink(user.full_name, f"tg://user?id={user_tg_id}")
            response = (

                f"Foydalanuvchi: {touch_user}\n"
                f"O'qilgan kitobi: {book_report.book}\n"
                f"Nechi kunda o'qigani: {book_report.reading_day}\n"
                f"O'qilgan sahifalar soni: {book_report.pages_read}\n"
                f"Guruhi: {user_topic_id}"
            )
        else:
            if user.full_name:
                mention = hlink(user.full_name, f"tg://user?id={user_tg_id}")
            elif user.username:
                mention = hlink("@" + user.username, f"tg://user?id={user_tg_id}")
            else:
                mention = hlink("Ism qo'yilmagan", f"tg://user?id={user_tg_id}")
            response = f"{mention} hech qanday kitob o'qimagan!"

        await message.answer(response)
    except TelegramProfile.DoesNotExist:
        await message.answer("Foydalanuvchi topilmadi. Iltimos, to'g'ri ID kiriting.")

    await state.finish()
