from aiogram.fsm.state import State, StatesGroup

    
class EventActions(StatesGroup):
    waiting_event_title = State()
    waiting_title_for_delete_event = State()
  
  
class AdminActions(StatesGroup):
    """ 
        Состояния действий администратора.
    
        - waiting_input_amount: Ожидание ввода суммы для списания.
        - waiting_title: Ожидание ввода названия нового события.
        - waiting_date: Ожидание ввода даты проведения события.
        - waiting_description: Ожидание ввода описания события.
        - waiting_input_balance_up_amount: Ожидание ввода суммы для пополнения баланса.
    """
    waiting_input_amount = State()
    waiting_title = State()
    waiting_date = State()
    waiting_description = State()
    waiting_input_balance_up_amount = State()
    
class MenuActions(StatesGroup):
    """ 
        Состояния управления меню.
        
        - waiting_title: Ожидание ввода названия нового элемента меню.
        - waiting_price: Ожидание ввода цены нового элемента меню.
        - waiting_picture: Ожидание отправки фотографии нового элемента меню.
        - waiting_title_for_delete: Ожидание ввода названия элемента меню для удаления.
    """
    waiting_title = State()
    waiting_price = State()
    waiting_picture = State()
    waiting_title_for_delete = State()