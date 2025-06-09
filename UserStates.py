from aiogram.fsm.state import State, StatesGroup

# تعریف حالت‌های FSM
class UserStates(StatesGroup):
    """States for the Telegram bot FSM"""
    browse_categories = State()
    view_product = State()
    view_service = State()
    view_category = State()
    view_educational_content = State()
    inquiry_name = State()
    inquiry_phone = State()
    inquiry_description = State()
    waiting_for_confirmation = State()
    waiting_for_search = State()