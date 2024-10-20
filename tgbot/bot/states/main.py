from aiogram.dispatcher.filters.state import State, StatesGroup

class AdmissionState(StatesGroup):
    language = State()
    full_name = State()
    phone_number = State()
    
class ReportState(StatesGroup):
    reading_day = State()
    book_title = State()
    pages_read = State()
    confirm_report = State()
    
class ChangeLanguageState(StatesGroup):
    language_change = State()

class GroupStates(StatesGroup):
    group = State()
    