from aiogram.fsm.state import State, StatesGroup


class AdminActions(StatesGroup):
    waiting_title = State()
    waiting_date = State()
    waiting_description = State()
    
    waiting_input_amount = State()
    waiting_for_qr_code = State()
    waiting_debit_confirmation = State()
    
    
class EventActions(StatesGroup):
    waiting_event_title = State()
    waiting_event_date = State()
    waiting_for_event_info = State()