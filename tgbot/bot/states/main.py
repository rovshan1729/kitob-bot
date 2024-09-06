from aiogram.dispatcher.filters.state import State, StatesGroup

class AdmissionState(StatesGroup):
    language = State()
    full_name = State()
    phone_number = State()
    email = State()
    skill = State()
    plan = State()
    keyboard_answer = State()
