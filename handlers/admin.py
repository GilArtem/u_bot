from datetime import datetime

from aiogram.filters import Command
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.errors import safe_send_message
from database.req_admin import *
from database.req_event import create_event

from instance import bot


router = Router()

class AdminActions(StatesGroup):
    waiting_title = State()
    waiting_date = State()
    waiting_description = State()
    
    
@router.message(Command('new_event'))
async def cmd_new_event(message: Message, state: FSMContext):
    user_admin = await get_user_admin(message.from_user.id)
    if not user_admin:
        await safe_send_message(bot, message, text = 'У Вас нет прав администратора.')
        return
    
    await safe_send_message(bot, message, text = 'Введите название нового ивента:')
    await state.set_state(AdminActions.waiting_title)
    
@router.message(AdminActions.waiting_title)
async def title_chosen(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await safe_send_message(bot, message, text = 'Введите дату проведения ивента (формат ГГГГ-ММ-ДД):')
    await state.set_state(AdminActions.waiting_date)
    
@router.message(AdminActions.waiting_date)
async def date_chosen(message: Message, state: FSMContext):
    try:
        event_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        await state.update_data(date=event_date)
        await safe_send_message(bot, message, text = 'Введите описание ивента:')
        await state.set_state(AdminActions.waiting_description)
    except ValueError:
        await safe_send_message(bot, message, text = "Неверный формат даты. Введите данные формата: ГГГГ-ММ-ДД.")

@router.message(AdminActions.waiting_description)
async def description_chosen(message: Message, state: FSMContext):
    data = await state.get_data()
    event_title = data['title']
    event_date = data['date']
    event_description = message.text

    await create_event(event_title, event_date, event_description, menu='Меню')
    
    await safe_send_message(bot, message, text = f'Ивент: {event_title}.\nДата проведения: {event_date}.\nОписание:\n\n{event_description}.')
    await state.clear()



@router.message(Command('send_event_to_users'))
async def cmd_send_event_to_users(message: Message):
    pass


@router.message(Command('add_new_admin'))
async def cmd_add_new_admin(message: Message):
    pass


@router.message(Command('scan_qr_code'))
async def cmd_scan_qr_code(message: Message):
    pass

