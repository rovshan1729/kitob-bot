import os
from aiogram import types
from aiogram.dispatcher import FSMContext
from tgbot.bot.keyboards.inline import languages_markup
from tgbot.bot.utils import get_user, get_lang
from tgbot.bot.keyboards.reply import main_markup, generate_custom_markup
# from tgbot.bot.states.main import MainState
from tgbot.bot.utils import get_user
from tgbot.bot.loader import dp, gettext as _
from django.utils import timezone
from utils.bot import get_model_queryset
from utils.bot import get_object_value, parse_telegram_message
from django.conf import settings
from tgbot.models import TelegramButton, TelegramProfile
from django.db.models import Q


# @dp.message_handler(state=MainState.dynamic_button, text=_("🔙 Orqaga"))
# async def back_to_prev(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     lang = data.get("language")
#     if not lang:
#         user = get_user(message.from_user.id)
#         if user:
#             lang = user.language

#     button_history = data.get("button_history", [])

#     if button_history:
#         # Pop the last visited button ID
#         last_button_id = button_history.pop()
#         await state.update_data({"button_history": button_history})

#         # Get the parent button
#         parent_button = TelegramButton.objects.filter(id=last_button_id).first()

#         if parent_button:
#             parent_id = parent_button.parent_id
#             if parent_id:
#                 child_buttons = TelegramButton.objects.filter(parent_id=parent_id)
#                 await message.answer(get_object_value(parent_button, "text", lang),
#                                      reply_markup=generate_custom_markup(child_buttons, lang),
#                                      disable_web_page_preview=True)
#                 await state.update_data({"current_button": parent_id})
#             else:
#                 await message.answer(_("Bosh menyu!"), reply_markup=main_markup(lang))
#                 await state.finish()
#         else:
#             await message.answer(_("Bosh menyu!"), reply_markup=main_markup(lang))
#             await state.finish()
#     else:
#         await message.answer(_("Bosh menyu!"), reply_markup=main_markup(lang))
#         await state.finish()


# @dp.message_handler(state=MainState.dynamic_button)
# async def dynamic_button(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     lang = data.get("language")
#     if not lang:
#         user = get_user(message.from_user.id)
#         if user:
#             lang = user.language

#     clicked_button = TelegramButton.objects.filter(
#         Q(title=message.text) | Q(title_uz=message.text) | Q(title_ru=message.text) | Q(title_en=message.text)
#     ).first()

#     if clicked_button:
#         child_buttons = TelegramButton.objects.filter(parent=clicked_button.id)
#         if child_buttons.exists():
#             await message.answer(get_object_value(clicked_button, "text", lang),
#                                  reply_markup=generate_custom_markup(child_buttons, lang),
#                                  disable_web_page_preview=True)
#             await state.update_data({"current_button": clicked_button.id})
#             button_history = data.get("button_history", [])
#             button_history.append(clicked_button.id)
#             await state.update_data({"button_history": button_history})

#         elif clicked_button.content:
#             content_url = os.path.join(settings.BACK_END_URL, clicked_button.content.url.lstrip('/'))
#             extension = os.path.splitext(clicked_button.content.name)[1].lower()
#             try:
#                 if extension in ['.jpg', '.jpeg', '.png']:
#                     response = await message.answer_photo(content_url, disable_notification=True,
#                                                           caption=parse_telegram_message(
#                                                               get_object_value(clicked_button, "text", lang)))
#                     if not clicked_button.file_id:
#                         clicked_button.file_id = response.photo[-1].file_id
#                         clicked_button.save(update_fields=['file_id'])
#                 elif extension in ['.mp4']:
#                     response = await message.answer_video(content_url, disable_notification=True,
#                                                           caption=parse_telegram_message(
#                                                               get_object_value(clicked_button, "text", lang)))
#                     if not clicked_button.file_id:
#                         clicked_button.file_id = response.video.file_id
#                         clicked_button.save(update_fields=['file_id'])
#                 elif extension in ['.gif', '.mov']:
#                     response = await message.answer_animation(content_url, disable_notification=True,
#                                                               caption=parse_telegram_message(
#                                                                   get_object_value(clicked_button, "text", lang)))
#                     if not clicked_button.file_id:
#                         clicked_button.file_id = response.animation.file_id
#                         clicked_button.save(update_fields=['file_id'])
#                 else:
#                     await message.answer(get_object_value(clicked_button, "text", lang))
#             except Exception as e:
#                 print(e, 'error')
#                 await message.answer(get_object_value(clicked_button, "text", lang))
#         else:
#             await message.answer(clicked_button.text)
#     else:
#         await message.answer(_("Bunday tugma mavjud emas!"), reply_markup=main_markup(lang))
#         await state.finish()


# @dp.message_handler(state="*")
# async def main_menu(message: types.Message, state: FSMContext):
#     if message.text:
#         clicked_button = TelegramButton.objects.filter(
#             Q(title=message.text) | Q(title_uz=message.text) | Q(title_ru=message.text) | Q(title_en=message.text)
#         ).first()
#         if clicked_button:
#             data = await state.get_data()
#             lang = data.get("language")
#             if not lang:
#                 user = get_user(message.from_user.id)
#                 if user:
#                     lang = user.language

#             child_buttons = TelegramButton.objects.filter(parent=clicked_button.id)
#             if child_buttons.exists():
#                 await message.answer(get_object_value(clicked_button, "text", lang),
#                                      reply_markup=generate_custom_markup(child_buttons, lang),
#                                      disable_web_page_preview=True)
#                 button_history = data.get("button_history", [])
#                 button_history.append(clicked_button.id)
#                 await state.update_data({"current_button": clicked_button.id, "button_history": button_history})
#                 await MainState.dynamic_button.set()
#             elif clicked_button.content:
#                 content_url = os.path.join(settings.BACK_END_URL, clicked_button.content.url.lstrip('/'))
#                 extension = os.path.splitext(clicked_button.content.name)[1].lower()
#                 try:
#                     if extension in ['.jpg', '.jpeg', '.png']:
#                         response = await message.answer_photo(content_url, disable_notification=True,
#                                                               caption=parse_telegram_message(
#                                                                   get_object_value(clicked_button, "text", lang)))
#                         if not clicked_button.file_id:
#                             clicked_button.file_id = response.photo[-1].file_id
#                             clicked_button.save(update_fields=['file_id'])
#                     elif extension in ['.mp4']:
#                         response = await message.answer_video(content_url, disable_notification=True,
#                                                               caption=parse_telegram_message(
#                                                                   get_object_value(clicked_button, "text", lang)))
#                         if not clicked_button.file_id:
#                             clicked_button.file_id = response.video.file_id
#                             clicked_button.save(update_fields=['file_id'])
#                     elif extension in ['.gif', '.mov']:
#                         response = await message.answer_animation(content_url, disable_notification=True,
#                                                                   caption=parse_telegram_message(
#                                                                       get_object_value(clicked_button, "text", lang)))
#                         if not clicked_button.file_id:
#                             clicked_button.file_id = response.animation.file_id
#                             clicked_button.save(update_fields=['file_id'])
#                     else:
#                         await message.answer(get_object_value(clicked_button, "text", lang))
#                 except Exception as e:
#                     print(e, 'error')
#                     await message.answer(get_object_value(clicked_button, "text", lang))
#             else:
#                 await message.answer(clicked_button.text)
