from aiogram.fsm.state import State, StatesGroup

    
class EventActions(StatesGroup):
    waiting_event_title = State()
    waiting_event_date = State()

    
class AdminActions(StatesGroup):
    waiting_input_amount = State()
    waiting_title = State()
    waiting_date = State()
    waiting_description = State()
    
    # Кнопка отмены админ
    waiting_get_approval = State()
