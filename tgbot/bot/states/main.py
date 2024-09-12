from aiogram.dispatcher.filters.state import State, StatesGroup

class AdmissionState(StatesGroup):
    language = State()
    full_name = State()
    phone_number = State()
    
class ReportState(StatesGroup):
    enter_reading_day = State()
    enter_book_title = State()
    enter_pages_read = State()
    confirm_report = State()
    
class ChangeLanguageState(StatesGroup):
    language_change = State()
    