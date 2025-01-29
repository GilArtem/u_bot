from aiogram.fsm.state import State, StatesGroup

    
class EventActions(StatesGroup):
    waiting_event_title = State()
  
  
class AdminActions(StatesGroup):
    waiting_input_amount = State()
    waiting_title = State()
    waiting_date = State()
    waiting_description = State()
    
    
class MenuActions(StatesGroup):
    waiting_curr_position = State()
    waiting_title = State()
    waiting_price = State()
    waiting_picture = State()
    waiting_title_for_delete = State()