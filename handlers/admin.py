from datetime import datetime

from sqlalchemy import select

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.models import TransactionRequest, async_session
from database.req_admin import get_user_admin
from database.req_event import create_event, get_event_by_title_and_date
from database.req_user import get_user
from database.req_admin import debit_balance
from database.req_transaction import create_transaction

from handlers.states import AdminActions, EventActions
from handlers.errors import safe_send_message

from keyboards.keyboards import confirmation_keyboard
from utils.notify_all_users import notify_all_users

from instance import bot, logger


router = Router()



# handlers/admin.py
@router.message(Command('scan_qr_code'))
async def cmd_scan_qr_code(message: Message, state: FSMContext, user_id: int):
    user_admin = await get_user_admin(message.from_user.id)
    if not user_admin:
        await safe_send_message(bot, message, text='У Вас нет прав администратора.')
        return 
    user = await get_user(user_id)
    if not user:
        await safe_send_message(bot, message, text='Пользователь не найден')
        return
    else:
        await safe_send_message(bot, message, text=f"Информация о пользователе:\nИмя: {user.name}\nБаланс: {user.balance}")
        await safe_send_message(bot, message, text='Введите сумму списания:')
        await state.update_data(user_id=user_id, admin_id=message.from_user.id)
        await state.set_state(AdminActions.waiting_input_amount)


@router.message(AdminActions.waiting_input_amount)
async def debit_amount_chosen(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await safe_send_message(bot, message, text='Неверный формат суммы. Введите число.')
        return 
    data = await state.get_data()
    user_id = data.get('user_id')
    user = await get_user(user_id)
    if not user:
        await safe_send_message(bot, message, text='Пользователь не найден.')
        await state.clear()
        return
    if user.balance >= amount:  
        await safe_send_message(bot, user_id, text=f'Администратор запросил списание {amount} рублей.\nПодтвердите операцию?', reply_markup=confirmation_keyboard)
        # Сохраняем данные для пользователя
        await state.update_data(amount=amount)
        await create_transaction(user_id, message.from_user.id, amount)  # Создаем запись о транзакции
    else:
        await safe_send_message(bot, message, text='Недостаточно средств на балансе.')
        await state.clear()

# Функция для создания записи о транзакции
async def create_transaction(user_id: int, admin_id: int, amount: float):
    async with async_session() as session:
        transaction_request = TransactionRequest(admin_id=admin_id, user_id=user_id, amount=amount, status='in_process')
        session.add(transaction_request)
        await session.commit()

# handlers/admin.py
@router.message(AdminActions.waiting_debit_confirmation)
async def confirm_debit(message: Message, state: FSMContext):
    # Этот обработчик больше не нужен, так как мы используем кнопки
    pass









































# # handlers/admin.py
# @router.message(Command('scan_qr_code'))
# async def cmd_scan_qr_code(message: Message, state: FSMContext, user_id: int):
#     user_admin = await get_user_admin(message.from_user.id)
#     if not user_admin:
#         await safe_send_message(bot, message, text='У Вас нет прав администратора.')
#         return 
#     user = await get_user(user_id)
#     if not user:
#         await safe_send_message(bot, message, text='Пользователь не найден')
#         return
#     else:
#         await safe_send_message(bot, message, text=f"Информация о пользователе:\nИмя: {user.name}\nБаланс: {user.balance}")
#         await safe_send_message(bot, message, text='Введите сумму списания:')
#         await state.update_data(user_id=user_id, admin_id=message.from_user.id)
#         await state.set_state(AdminActions.waiting_input_amount)

# @router.message(AdminActions.waiting_input_amount)
# async def debit_amount_chosen(message: Message, state: FSMContext):
#     try:
#         amount = float(message.text)
#     except ValueError:
#         await safe_send_message(bot, message, text='Неверный формат суммы. Введите число.')
#         return 
#     data = await state.get_data()
#     user_id = data.get('user_id')
#     user = await get_user(user_id)
#     if not user:
#         await safe_send_message(bot, message, text='Пользователь не найден.')
#         await state.clear()
#         return
#     if user.balance >= amount:  
#         await safe_send_message(bot, user_id, text=f'Администратор запросил списание {amount} рублей.\nПодтвердите операцию?', reply_markup=confirmation_keyboard())
#         # Сохраняем данные для пользователя
#         await state.update_data(amount=amount)
#         request = TransactionRequest(admin_id=message.from_user.id, user_id=user_id, amount=amount)
#         async with async_session() as session:
#             session.add(request)
#             await session.commit()
#         await state.set_state(AdminActions.waiting_debit_confirmation)
#     else:
#         await safe_send_message(bot, message, text='Недостаточно средств на балансе.')
#         await state.clear()

# @router.message(AdminActions.waiting_debit_confirmation)
async def confirm_debit(message: Message, state: FSMContext):
    # logger.info(f"Получено подтверждение: {message.text} от admin_id={message.from_user.id}")
    # if message.text.lower() not in ['да', 'yes']:
    #     await safe_send_message(bot, message, text='Подтвердите операцию, введя "да" или "yes".')
    #     return
    # data = await state.get_data()
    # user_id = data.get('user_id')
    # admin_id = data.get('admin_id')
    # amount = data.get('amount')
    # if not all([user_id, admin_id, amount]):
    #     await safe_send_message(bot, message, text='Ошибка: недостаточно данных для подтверждения операции.')
    #     logger.error("Недостаточно данных для выполнения списания")
    #     await state.clear()
    #     return
    # try:
    #     async with async_session() as session:
    #         request = await session.execute(
    #             select(TransactionRequest).where(
    #                 TransactionRequest.admin_id == admin_id,
    #                 TransactionRequest.user_id == user_id,
    #                 TransactionRequest.amount == amount,
    #                 TransactionRequest.status == 'in_process'
    #             )
    #         )
    #         request = request.scalar_one_or_none()
    #         if request:
    #             debit_success = await debit_balance(user_id, amount)
    #             if debit_success:
    #                 request.status = 'completed'
    #                 await session.commit()
    #                 await safe_send_message(bot, message, text='Средства успешно списаны.')
    #                 await safe_send_message(bot, user_id, text=f'С вашего баланса списано {amount} рублей.')
    #                 await safe_send_message(bot, admin_id, text='Операция успешно выполнена и подтверждена.')
    #             else:
    #                 await safe_send_message(bot, message, text='Ошибка: недостаточно средств на балансе.')
    #         else:
    #             await safe_send_message(bot, message, text='Транзакция уже завершена или отменена.')
    # except Exception as e:
    #     logger.error(f"Ошибка при подтверждении списания: {e}")
    #     await safe_send_message(bot, message, text='Произошла ошибка. Попробуйте позже.')
    # finally:
    #     await state.clear()
    
        








# @router.message(Command('scan_qr_code'))
# async def cmd_scan_qr_code(message: Message, state: FSMContext, user_id: int):
#     user_admin = await get_user_admin(message.from_user.id)
#     if not user_admin:
#         await safe_send_message(bot, message, text = 'У Вас нет прав администратора.')
#         return 
    
#     # #########
#     # # Извлекаем user_id из текста сообщения
#     # try:
#     #     user_id_str = message.get_args()
#     #     user_id = int(user_id_str)
#     # except (AttributeError, ValueError):
#     #     await safe_send_message(bot, message, text='Неверный формат QR-кода.')
#     #     return
#     # #########
    
#     user = await get_user(user_id)
#     if not user:
#         await safe_send_message(bot, message, text = 'Пользователь не найден')
#         return
#     else:
#         await safe_send_message(bot, message, text = f"Информация о пользователе:\nИмя: {user.name}\nБаланс: {user.balance}")
#         await safe_send_message(bot, message, text = 'Введите сумму списания:')
#         await state.update_data(user_id=user_id, admin_id=message.from_user.id)
#         await state.set_state(AdminActions.waiting_input_amount)
       

# @router.message(AdminActions.waiting_input_amount)
# async def debit_amount_chosen(message: Message, state: FSMContext):
#     try:
#         amount = float(message.text)
#     except ValueError:
#         await safe_send_message(bot, message, text = 'Неверный формат суммы. Введите число.')
#         return 
    
#     data = await state.get_data()
#     user_id = data.get('user_id')
#     user = await get_user(user_id)
    
#     if not user:
#         await safe_send_message(bot, message, text='Пользователь не найден.')
#         await state.clear()
#         return
    
#     if user.balance >= amount:  
#         await safe_send_message(bot, user_id, text=f'Администратор запросил списание {amount} рублей.\nПодтвердите операцию?')
#         # ПЕРЕЛОМ 
#         # Сохраняем данные для пользователя
#         await state.update_data(amount=amount)
#         await state.set_state(AdminActions.waiting_debit_confirmation)
#     else:
#         await safe_send_message(bot, message, text='Недостаточно средств на балансе.')
#         await state.clear()

# @router.message(AdminActions.waiting_debit_confirmation)
# async def confirm_debit(message: Message, state: FSMContext):
#     logger.info(f"Получено подтверждение: {message.text} от admin_id={message.from_user.id}")

#     if message.text.lower() not in ['да', 'yes']:
#         await safe_send_message(bot, message, text='Подтвердите операцию, введя "да" или "yes".')
#         return

#     data = await state.get_data()
#     user_id = data.get('user_id')
#     admin_id = data.get('admin_id')
#     amount = data.get('amount')

#     if not all([user_id, admin_id, amount]):
#         await safe_send_message(bot, message, text='Ошибка: недостаточно данных для подтверждения операции.')
#         logger.error("Недостаточно данных для выполнения списания")
#         await state.clear()
#         return

#     try:
#         debit_success = await debit_balance(user_id, amount)
#         if debit_success:
#             await safe_send_message(bot, message, text='Средства успешно списаны.')
#             await safe_send_message(bot, user_id, text=f'С вашего баланса списано {amount} рублей.')
#             await safe_send_message(bot, admin_id, text='Операция успешно выполнена и подтверждена.')
#         else:
#             await safe_send_message(bot, message, text='Ошибка: недостаточно средств на балансе.')
#     except Exception as e:
#         logger.error(f"Ошибка при подтверждении списания: {e}")
#         await safe_send_message(bot, message, text='Произошла ошибка. Попробуйте позже.')
#     finally:
#         await state.clear()
# @router.message(AdminActions.waiting_debit_confirmation)
# async def confirm_debit(message: Message, state: FSMContext):
#     if message.text.lower() == 'да':
        
#         data = await state.get_data()
#         user_id = data.get('user_id')
#         admin_id = data.get('admin_id')
#         amount = data.get('amount')
        
#         if user_id and amount and admin_id:
#             user = await get_user(user_id)
#             if user and user.balance >= amount:
#                 debit_success = await debit_balance(user_id, amount)
#                 if debit_success:
#                     await safe_send_message(bot, message, text='Средства успешно списаны.')
#                     await safe_send_message(bot, user_id, text=f'С вашего баланса списано {amount} рублей.')
#                     await safe_send_message(bot, admin_id, text='Операция подтверждена пользователем.')
#                     await state.clear()
#                 else:
#                     await safe_send_message(bot, message, text='Ошибка при списании средств.')
#             else:
#                 await safe_send_message(bot, message, text='Недостаточно средств на балансе.')
#         else:
#             await safe_send_message(bot, message, text='Недостаточно данных для подтверждения.')
#     else:
#         await safe_send_message(bot, message, text='Подтвердите операцию, введя "да" или "yes".')


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
    menu_id = None
    
    await create_event(event_title, event_date, event_description, menu_id)
    
    await safe_send_message(bot, message, text = f'Ивент: {event_title}.\nДата проведения: {event_date}.\nОписание:\n\n{event_description}.')
    await state.clear()


@router.message(Command('send_event_to_users'))
async def cmd_send_event_to_users(message: Message, state: FSMContext):
    user_admin = await get_user_admin(message.from_user.id)
    if user_admin:
        await state.set_state(EventActions.waiting_event_title)
        await safe_send_message(bot, message, text = "Введите название ивента:")
    else:
        await safe_send_message(bot, message, text = 'У Вас нет прав администратора.') 
        
        
@router.message(EventActions.waiting_event_title)
async def title_event_chosen(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(EventActions.waiting_event_date)
    await safe_send_message(bot, message, text = 'Введите дату проведения ивента (формат YYYY-MM-DD):')
    

@router.message(EventActions.waiting_event_date)
async def date_event_chosen(message: Message, state: FSMContext):
    event_date = datetime.strptime(message.text, "%Y-%m-%d").date()
    data = await state.get_data()
    title = data.get('title')
    event = await get_event_by_title_and_date(title, event_date)
        
    if event:
        await notify_all_users(event.title, event.date, event.description)
        await safe_send_message(bot, message, text = 'Информация о ивенте передана пользователям.')
        await state.clear()
    else:
        await safe_send_message(bot, message, text = 'Ивент с указанным названием и датой не найден. Попробуйте еще раз.')
        await state.set_state(EventActions.waiting_event_title)
    

