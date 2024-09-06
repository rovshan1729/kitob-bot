import re
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.utils.exceptions import MessageNotModified, MessageToDeleteNotFound
from django.db.models import Q

from tgbot.models import TelegramProfile, Skill, SelectPlan, PlanButtons
from tgbot.bot.keyboards.inline import languages_markup, get_check_button, get_skills_markup
from tgbot.bot.keyboards.reply import (
    phone_keyboard, 
    main_markup, 
    main_menu_markup, 
    select_plan, 
    plan_button,
    back_keyboard
    )
from tgbot.bot.loader import dp, bot
from tgbot.bot.loader import gettext as _
from tgbot.bot.states.main import AdmissionState
from tgbot.bot.utils import get_user, get_lang
from utils.subscription import get_result
from aiogram.utils.callback_data import CallbackData



async def do_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(message.from_user.id)
        if user:
            lang = user.language
    check_subs_message_id = data.get("check_subs_message_id")
    if check_subs_message_id:
        try:
            await bot.delete_message(message.from_user.id, check_subs_message_id)
        except MessageToDeleteNotFound:
            print("Delete is not working correctly!")
    user = TelegramProfile.objects.filter(telegram_id=message.from_user.id).first()
    if not user:
        TelegramProfile.objects.create(telegram_id=user.id, email=user.email,
                                       username=user.username, language=user.language_code,
                                       full_name=user.full_name)
    if not user.is_registered:
        await message.answer(
            text='Marhamat tilni tanlang! 🇺🇿\nПожалуйста, выберите язык! 🇷🇺\nPlease, select a language! 🇺🇸',
            reply_markup=languages_markup)
        await AdmissionState.language.set()
    else:
        await message.answer(_("Siz so'rovni allaqachon to'ldirdingiz."))


@dp.message_handler(CommandStart(), state="*")
async def bot_start(message: types.Message, state: FSMContext):
    await state.finish()

    final_status, chat_ids = await get_result(user_id=message.from_user.id)

    reply_markup = await get_check_button(chat_ids)

    if not final_status:
        if reply_markup:
            check_subs_message = await message.answer(
                _(f"Quyidagi kanallarga obuna bo'lishingiz kerak, pastdagi tugmalar ustiga bosing ⬇️\n\n"
                  f"Вам необходимо подписаться на следующие каналы, нажмите на кнопки ниже ⬇️\n\n"
                  f"You must subscribe to the following channels, click on the buttons below ⬇️"),
                reply_markup=reply_markup,
                disable_web_page_preview=True)
            await state.update_data({"check_subs_message_id": check_subs_message.message_id})
        else:
            await do_start(message, state)
    else:
        await do_start(message, state)


@dp.callback_query_handler(text="check_subs")
async def checker(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        user = get_user(call.message.from_user.id)
        if user:
            lang = user.language

    final_status, chat_ids = await get_result(user_id=call.from_user.id)
    if final_status:
        data = await state.get_data()
        check_subs_message_id = data.get("check_subs_message_id")
        if check_subs_message_id:
            try:
                await bot.delete_message(call.from_user.id, check_subs_message_id)
            except MessageToDeleteNotFound:
                await call.message.delete()
        user = TelegramProfile.objects.filter(telegram_id=call.from_user.id).first()
        if not user:
            TelegramProfile.objects.create(telegram_id=user.id, email=user.email,
                                           username=user.username, language=user.language_code,
                                           full_name=user.full_name)
        if not user.is_registered:
            await call.message.answer(
                text='Marhamat tilni tanlang! 🇺🇿\nПожалуйста, выберите язык! 🇷🇺\nPlease, select a language! 🇺🇸',
                reply_markup=languages_markup)
            await AdmissionState.language.set()
        else:
            await call.message.answer(_("Siz so'rovni allaqachon to'ldirdingiz."))
    else:
        reply_markup = await get_check_button(chat_ids)
        if not reply_markup:
            await call.message.delete()
            await call.answer(_("Barcha kanallarga obuna bo'ldingiz!"))
        else:
            try:
                await call.message.edit_reply_markup(reply_markup=reply_markup)
            except MessageNotModified:
                await call.answer(_("Siz obuna bo'lmagan kanallar mavjud!"), show_alert=True)


@dp.message_handler(state=AdmissionState.language)
async def language(message: types.Message, state: FSMContext):
    lang = message.text
    user = get_user(message.from_user.id)
    if not user.is_registered:
        if lang == "O'zbekcha":
            await message.answer("Iltimos, familiyangizni, ismingizni va otangizning ismini kiriting ⬇️",
                                 reply_markup=back_keyboard)
            await AdmissionState.full_name.set()
        elif lang == "Русский":
            await message.answer("️Пожалуйста, напишите, свою фамилию, имя и отчество ⬇️",
                                 reply_markup=back_keyboard)
            await AdmissionState.full_name.set()
        elif lang == "English":
            await message.answer("Please, enter your surname, name and middle name ⬇️",
                                 reply_markup=back_keyboard)
            await AdmissionState.full_name.set()
        elif lang == "Qaraqalpaqsha":
            await message.answer("Ótinish, famılıyańızdı, atıńızdı hám otangizning atın kiritiń ⬇️",
                                 reply_markup=back_keyboard)
            await AdmissionState.full_name.set()
        else:
            await message.answer("Iltimos Tugmalardan birini tanlang 🇺🇿\n\n"
                                 "Пожалуйста, выберите одну из кнопок 🇷🇺\n\n"
                                 "Please, select one of the buttons 🇺🇸", reply_markup=languages_markup)
    else:
        await message.answer(_("Siz qilgan o'zgarishlar saqlandi, iltimos botni /start bosib qayta ishga tushiring"),
                             reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
    user.language = get_lang(lang)
    user.save(update_fields=['language'])
    # We need get language from DB not from state memory
    # await state.update_data({"language": user.language})


@dp.message_handler(state=AdmissionState.full_name)
async def full_name(message: types.Message, state: FSMContext):
    full_name_text = message.text.strip()
    is_correct = full_name_text.split(' ')

    if len(is_correct) >= 2 and len(full_name_text) <= 128:
        await state.update_data({"full_name": full_name_text})
        await message.answer(_('Telefon raqamingizni quyidagi tugmani bosgan holda yuboring.'),
                             reply_markup=phone_keyboard)
        await AdmissionState.phone_number.set()
    elif len(full_name_text) > 128:
        await message.answer(_("Ismingiz 120 belgidan uzun bo'lmasligi kerak."))
    else:
        await message.answer(_("Faqat Text Formatda Kamida 2ta so'z bilan yozing"))



@dp.message_handler(state=AdmissionState.phone_number, content_types=types.ContentTypes.TEXT)
@dp.message_handler(state=AdmissionState.phone_number, content_types=types.ContentTypes.CONTACT)
async def contact_handler(message: types.Message, state: FSMContext):
    if message.content_type in types.ContentTypes.TEXT:
        await message.answer(_("Pastdagi tugma orqali raqamingizni yuboring"))
    elif message.content_type in types.ContentTypes.CONTACT and message.contact.phone_number and message.from_user.id == message.contact.user_id:
        await state.update_data({"phone_number": message.contact.phone_number})
        await message.answer(_("Email ni yuvoring"), reply_markup=back_keyboard)
        await AdmissionState.email.set()
    else:
        await message.answer(_('📲 Iltimos Raqamni Yuborish Tugmasini Bosing'))
        

import re

@dp.message_handler(state=AdmissionState.email, content_types=types.ContentTypes.TEXT)
async def skill(message: types.Message, state: FSMContext):
    email = message.text
    user = get_user(message.from_user.id)
    language = user.language
    
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await state.update_data(email=email)
        
        await message.answer(_("Email qabul qilindi! Iltimos, o'z mahoratingizni tanlang."), reply_markup=back_keyboard)

        root_skills = Skill.objects.filter(parent__isnull=True)
        markup = get_skills_markup(root_skills, language=language)
        await message.answer("Select a skill:", reply_markup=markup)
        return await AdmissionState.skill.set()
    else:
        await message.answer(_("❌ Iltimos, to'g'ri email manzilini kiriting."))
        
skill_cb = CallbackData('skill', 'id', 'level', 'action', 'page')
       

@dp.callback_query_handler(skill_cb.filter(action='select'), state=AdmissionState.skill)
async def skill_selected(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    skill_id = int(callback_data['id'])
    skill = Skill.objects.get(id=skill_id)
    is_parent = False
    if skill.child.count() == 0:
        skills = Skill.objects.filter(parent__isnull=True)
    else:
        is_parent = True
        skills = skill.child.all()

    data = await state.get_data()
    if data.get("selected_skills", []) is not []:
        selected_skills = data.get("selected_skills", [])
    else:
        selected_skills = []
        
    if data.get("page", None) is not None:
        page = data.get('page', 0)
    else:
        page = 0
    
    if skill_id in selected_skills:
        selected_skills.remove(skill_id)
    else:
        if not is_parent:
            selected_skills.append(skill_id)
    
    await state.update_data(
        selected_skills=selected_skills
    )
    
    user = get_user(callback_query.from_user.id)
    language = user.language
    
    if is_parent:
        await callback_query.message.edit_text(
            text=f"Select a skill:",
            reply_markup=get_skills_markup(skills, page=page, selected_skills=selected_skills, parent_id=skill.id, language=language)
        )
    else:
        await callback_query.message.edit_text(
            text=f"Select a skill:",
            reply_markup=get_skills_markup(skills, page=page, selected_skills=selected_skills, language=language)
        )

@dp.callback_query_handler(skill_cb.filter(action='parent'), state=AdmissionState.skill)
async def skill_parent(callback_query: types.CallbackQuery, callback_data: dict):
    skill_id = int(callback_data['id'])
    skill = Skill.objects.get(id=skill_id)
    
    user = get_user(callback_query.from_user.id)
    language = user.language

    if skill.parent:
        parent_skills = skill.parent.child.all()
        await callback_query.message.edit_text(
            text=f"Select a skill under {skill.parent.title}:",
            reply_markup=get_skills_markup(parent_skills, parent_id=skill.parent.id, language=language)
        )
    else:
        root_skills = Skill.objects.filter(parent__isnull=True)
        await callback_query.message.edit_text(
            text="Select a skill:",
            reply_markup=get_skills_markup(root_skills, language=language)
        )

@dp.callback_query_handler(skill_cb.filter(action='paginate'), state=AdmissionState.skill)
async def skill_paginate(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    page = int(callback_data['page'])
    
    data = await state.get_data()
    if data.get("selected_skills", []) is not []:
        selected_skills = data.get("selected_skills", [])
    else:
        selected_skills = []
        
    user = get_user(callback_query.from_user.id)
    language = user.language
    skills = Skill.objects.filter(parent__isnull=True)
    await state.update_data(
        page=page
    )
    
    await callback_query.message.edit_reply_markup(
        reply_markup=get_skills_markup(skills, page=page, language=language, selected_skills=selected_skills)
    )
    
@dp.callback_query_handler(skill_cb.filter(action='confirm'), state=AdmissionState.skill)
async def confirm_skills(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    user = get_user(call.from_user.id)
    lang = user.language
    selected_skills = data.get("selected_skills", [])
    
    if selected_skills is []:
        return await call.answer("Skill is required")
    
    select_plan_buttons = SelectPlan.objects.filter(parent=None)
    await state.update_data(select_plan_buttons=select_plan_buttons)
    
    await call.message.answer(_("Select your plan"), reply_markup=select_plan(select_plan_buttons, lang))
    
    await call.answer()
    
    await AdmissionState.plan.set()
    

@dp.message_handler(state=AdmissionState.plan)
async def select_plan_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    selected_button = message.text.strip()
    await state.update_data(selected_button=selected_button)
    user = get_user(message.from_user.id)
    language = user.language
    
    if message.text == _("🔙 Orqaga"):
        root_skills = Skill.objects.filter(parent__isnull=True)
        markup = get_skills_markup(root_skills, language=language)
        await message.answer("Select a skill", reply_markup=back_keyboard)
        await message.answer("Skills:", reply_markup=markup)
        return await AdmissionState.skill.set()
    
    plan = SelectPlan.objects.filter(Q(title_uz=selected_button) | Q(title_ru=selected_button) | 
                    Q(title_en=selected_button) | Q(title_qr=selected_button)).first()
        
    if not plan:
        await message.answer("Plan not found")
        
    text = getattr(plan, f"content_{language}", None)
    buttons = plan.buttons.all()
    button_obj = plan.buttons.first()
    button_content = getattr(button_obj, f"content_{language}", None)
    
    if plan.type == SelectPlan.AnswerChoice.TEXT_BUTTON:
        await message.answer(text, reply_markup=plan_button(buttons, language))
        
    elif plan.type == SelectPlan.AnswerChoice.TEXT_CV_LINK:
        await message.answer(text, reply_markup=plan_button(buttons, language))

    elif plan.type == SelectPlan.AnswerChoice.TEXT_LINK:
        await message.answer(text, reply_markup=plan_button(buttons, language))
        
    plan_type = plan.type
    await state.update_data(button_content=button_content, plan=plan, plan_type=plan_type)


    await AdmissionState.keyboard_answer.set()

    # saving data 
    user = TelegramProfile.objects.filter(
        telegram_id=message.from_user.id
    ).first()
    if user:
        user.full_name = data.get("full_name")
        user.phone_number = data.get("phone_number")
        user.email = data.get("email")
        user.skill.set(Skill.objects.filter(id__in=data.get('selected_skills')))
        user.plan = plan.title_en
        user.is_registered = True
        user.save()
    else:
        tguser = TelegramProfile.objects.create(
            telegram_id=message.from_user.id,
            full_name=data.get("full_name"),
            phone_number=data.get("phone_number"),
            email=data.get("email"),
            plan=plan,
            is_registered=True,
        )
        tguser.skill.set(Skill.objects.filter(id_in=data.get("selected_skills")))
        tguser.save()
        

    

@dp.message_handler(state=AdmissionState.keyboard_answer)
async def keyboard_answer_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = get_user(message.from_user.id)
    language = user.language
    select_plan_buttons = data.get('select_plan_buttons')
    
    if message.text == _("🔙 Orqaga"):
        await message.answer(_("Select your plan"), reply_markup=select_plan(select_plan_buttons, language))
        return await AdmissionState.plan.set()
    
    else:
        button_content = data.get("button_content")
        text = button_content
        await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
        
        await message.answer(_("You have completed our survey, our organization will contact you soon."))
        
        await state.reset_data()
        await state.finish()

