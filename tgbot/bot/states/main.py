from aiogram.dispatcher.filters.state import State, StatesGroup


class RegisterState(StatesGroup):
    language = State()
    subscribe = State()
    full_name = State()
    phone_number = State()
    birthday = State()
    region = State()
    district = State()
    school = State()
    class_ = State()


class OlympiadState(StatesGroup):
    choose_olympiad = State()
    confirm_start = State()
    rules = State()
    test = State()
    choose = State()
    see_results = State()
    get_certificate = State()
    get_rating = State()


class MainState(StatesGroup):
    main = State()
    change_language = State()
    dynamic_button = State()


class AdmissionState(StatesGroup):
    full_name = State()
    birth_date = State()
    phone = State()
    phone_2 = State()
    email = State()
    id = State()
    region = State()
    district = State()
    school = State()
    is_citizen = State()
    choice_form = State()
    gender = State()
    self_introduction = State()
    share_source_university = State()
    why_our_university = State()
    english_degree = State()
    add_document = State()
    collect_data = State()
    is_data_correct = State()
    change_language = State()
    # frient admission states
    friend_introduction = State()
    friend_share_source_university = State()
    friend_why_our_university = State()
    friend_english_degree = State()
    friend_add_document = State()
    friend_collect_data = State()
    friend_is_data_correct = State()

    about_university = State()



class OlimpicResultsState(StatesGroup):
    olimpics = State()
    olimpic = State()


class OlimpicRatingState(StatesGroup):
    olimpic = State()
    region = State()
    district = State()
    school = State()
    class_room = State()
    rating = State()