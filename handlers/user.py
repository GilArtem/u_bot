from aiogram.filters import Command, CommandStart, CommandObject
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

# ПОСЛЕДНЯЯ ВЕРСИЯ
from aiogram.types import Message, CallbackQuery as CQ

from sqlalchemy import select

from database.req_admin import debit_balance
from database.req_user import get_user, create_user
from database.req_menu import get_all_menu

from handlers.errors import safe_send_message
from handlers.admin import cmd_scan_qr_code

from utils.generate_qr_code import generate_qr_code

from keyboards.keyboards import menu_buttons, user_selection_button

from instance import bot, logger
from database.models import TransactionRequest, async_session


router = Router()



@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    hash_value = command.args  # scan_qr_code_user_12345
    
    if hash_value and hash_value.startswith('scan_qr_code_user_'):
        await cmd_scan_qr_code(message, state, hash_value)
    else:
        user = await get_user(message.from_user.id)
        if not user:
            await create_user(message.from_user.id, message.from_user.username)
        await safe_send_message(bot, message, text="Приветствуем тебя в нашем боте 'U', который станет твоим проводником и помощником на всех ивентах", reply_markup=menu_buttons())



@router.callback_query(F.data.in_(['confirm_user', 'cancel_user']))
async def handle_user_response(callback: CQ, state: FSMContext):      # Убрать state отсюда 
    logger.info(f"Получено подтверждение: {callback.data} от user_id={callback.from_user.id}")

    async with async_session() as session:
        
        request = await session.execute(
            select(TransactionRequest).where(
                TransactionRequest.user_id == callback.from_user.id,
                TransactionRequest.status == 'in_process',
            ).order_by(TransactionRequest.created_at.desc()).limit(1)
        )
        request = request.scalar_one_or_none()
        
        if not request:
            await callback.message.answer("Транзакция уже завершена или отменена.") # Почему тут колбэк?
            return
        
        if callback.data == 'confirm_user':
            debit_success = await debit_balance(request.user_id, request.amount)
            if debit_success:
                request.status = 'completed'
                await session.commit()
                await callback.message.answer("Операция подтверждена и завершена.")
                await bot.send_message(request.admin_id, "Пользователь подтвердил операцию.")
                await safe_send_message(bot, request.user_id, text=f'С вашего баланса списано {request.amount} рублей.')  # Тут указана сумма 23
                await safe_send_message(bot, request.admin_id, text='Операция успешно выполнена и подтверждена.')
            else:
                await callback.message.answer("Ошибка: недостаточно средств на балансе.")
                await safe_send_message(bot, request.admin_id, text='Ошибка: недостаточно средств на балансе.')
        elif callback.data == 'cancel_user':
            request.status = 'expired'   # Переводится как истек! Почему? поменять на отменена
            await session.commit()
            await callback.message.answer("Операция отменена.")
            await bot.send_message(request.admin_id, "Пользователь отменил операцию.")






























# @router.message(CommandStart())
# async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
#     hash_value = command.args  # scan_qr_code_user_12345
#     ## Переносим в FSM админа
#     if hash_value and hash_value.startswith('scan_qr_code_user_'):
#         await cmd_scan_qr_code(message, state, hash_value)
#     else:
#         user = await get_user(message.from_user.id)
#         if not user:
#             await create_user(message.from_user.id, message.from_user.username)
#         await safe_send_message(bot, message, text="Приветствуем тебя в нашем боте 'U', который станет твоим проводником и помощником на всех ивентах", reply_markup=menu_buttons())

# @router.callback_query(F.data.in_(['confirm_user', 'cancel_user']))
# async def handle_user_response(callback: CQ, state: FSMContext):
#     logger.info(f"Получено подтверждение: {callback.data} от user_id={callback.from_user.id}")

#     data = await state.get_data()
#     user_id = data.get('user_id')
#     admin_id = data.get('admin_id')
#     amount = data.get('amount')

#     if not all([user_id, admin_id, amount]):
#         await callback.message.answer('Ошибка: недостаточно данных для подтверждения операции.')
#         logger.error("Недостаточно данных для выполнения списания")
#         await state.clear()
#         return

#     async with async_session() as session:
#         request = await session.execute(
#             select(TransactionRequest).where(
#                 TransactionRequest.user_id == user_id,
#                 TransactionRequest.admin_id == admin_id,
#                 TransactionRequest.amount == amount,
#                 TransactionRequest.status == 'in_process'
#             ).order_by(TransactionRequest.created_at.desc()).limit(1)
#         )
#         request = request.scalar_one_or_none()
        
#         if not request:
#             await callback.message.answer("Транзакция уже завершена или отменена.")
#             await state.clear()
#             return
        
#         if callback.data == 'confirm_user':
#             debit_success = await debit_balance(request.user_id, request.amount)
#             if debit_success:
#                 request.status = 'completed'
#                 await session.commit()
#                 await callback.message.answer("Операция подтверждена и завершена.")
#                 await bot.send_message(request.admin_id, "Пользователь подтвердил операцию.")
#                 await safe_send_message(bot, user_id, text=f'С вашего баланса списано {amount} рублей.')
#                 await safe_send_message(bot, admin_id, text='Операция успешно выполнена и подтверждена.')
#             else:
#                 await callback.message.answer("Ошибка: недостаточно средств на балансе.")
#                 await safe_send_message(bot, admin_id, text='Ошибка: недостаточно средств на балансе.')
#         elif callback.data == 'cancel_user':
#             request.status = 'expired'
#             await session.commit()
#             await callback.message.answer("Операция отменена.")
#             await bot.send_message(request.admin_id, "Пользователь отменил операцию.")

#     await state.clear()





















## НОВЫЙ УДЕЛ 
# @router.message(CommandStart())
# async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
#     hash_value = command.args  # scan_qr_code_user_12345
#     if hash_value and hash_value.startswith('scan_qr_code_user_'):
#         try:
#             parts = hash_value.split('_')
#             user_id = int(parts[-1])
#         except (ValueError, IndexError):
#             await safe_send_message(bot, message, text='Неверный формат QR-кода.')
#             return
#         await cmd_scan_qr_code(message, state, user_id)
#     else:
#         user = await get_user(message.from_user.id)
#         if not user:
#             await create_user(message.from_user.id, message.from_user.username)
#         await safe_send_message(bot, message, text="Приветствуем тебя в нашем боте 'U', который станет твоим проводником и помощником на всех ивентах", reply_markup=menu_buttons())


 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
# @router.callback_query(F.data == 'confirm_user')
# async def confirm_transaction(callback: CallbackQuery, state: FSMContext):
#     user_id = callback.from_user.id
#     async with async_session() as session:
#         request = await session.execute(
#             select(TransactionRequest).where(
#                 TransactionRequest.user_id == user_id,
#                 TransactionRequest.status == 'in_process'
#             ).order_by(TransactionRequest.created_at.desc()).limit(1)  # Получаем самую последнюю запись
#         )
#         request = request.scalar_one_or_none()
#         if request:
#             debit_success = await debit_balance(request.user_id, request.amount)
#             if debit_success:
#                 request.status = 'completed'
#                 await session.commit()
#                 await callback.message.answer("Операция подтверждена и завершена.")
#                 await bot.send_message(request.admin_id, "Пользователь подтвердил операцию.")
#             else:
#                 await callback.message.answer("Ошибка: недостаточно средств на балансе.")
#         else:
#             await callback.message.answer("Транзакция уже завершена или отменена.")
            
            
# @router.callback_query(F.data == 'cancel_user')
# async def cancel_transaction(callback: CallbackQuery, state: FSMContext):
#     user_id = callback.from_user.id
#     async with async_session() as session:
#         request = await session.execute(
#             select(TransactionRequest).where(
#                 TransactionRequest.user_id == user_id,
#                 TransactionRequest.status == 'in_process'
#             ).order_by(TransactionRequest.created_at.desc()).limit(1)  # Получаем самую последнюю запись
#         )
#         request = request.scalar_one_or_none()
#         if request:
#             request.status = 'expired'
#             await session.commit()
#             await callback.message.answer("Операция отменена.")
#             await bot.send_message(request.admin_id, "Пользователь отменил операцию.")
#         else:
#             await callback.message.answer("Транзакция уже завершена или отменена.")    
    
    
    
    
    

# @router.message(CommandStart())
# async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
#     hash_value = command.args  # scan_qr_code_user_12345
#     if hash_value and hash_value.startswith('scan_qr_code_user_'):
#         # try:
#         #     parts = hash_value.split('_')
#         #     user_id = int(parts[-1])
#         # except (ValueError, IndexError):
#         #     await safe_send_message(bot, message, text='Неверный формат QR-кода.')
#         #     return
#         await cmd_scan_qr_code(message, command, state)
#     else:
#         user = await get_user(message.from_user.id)
#         if not user:
#             await create_user(message.from_user.id, message.from_user.username)
#         await safe_send_message(bot, message, text="Приветствуем тебя в нашем боте 'U', который станет твоим проводником и помощником на всех ивентах", reply_markup=menu_buttons())

    
    
    
    
    
    
    
    
        
        
@router.message(Command('info'))
async def cmd_info(message: Message):
    await safe_send_message(bot, message, text="Оставить тут информацию")


@router.message(Command('check_balance'))
@router.message((F.text == "Проверить баланс"))
async def cmd_check_balance(message: Message):
    user = await get_user(message.from_user.id) 
    await safe_send_message(bot, message, text = f'Ваш текущий баланс: {user.balance} руб.', reply_markup=menu_buttons())


@router.message(Command('balance_up'))
@router.message((F.text == "Пополнить баланс"))
async def cmd_balance_up(message: Message):
    user = await get_user(message.from_user.id)
    pass # Логика выполнения транзакции
   

@router.message(Command('show_qr_code'))
@router.message((F.text == "Показать QR"))
async def cmd_show_qr_code(message: Message):
    user_id = message.from_user.id
    qr_code = generate_qr_code(user_id)
    await message.answer_photo(photo=qr_code, caption="Покажите ваш уникальный QR-код администратору", reply_markup=menu_buttons())


@router.message(Command('show_menu'))
@router.message((F.text == "Меню"))
async def cmd_show_menu(message: Message):
    all_menu = await get_all_menu()  
    if all_menu:
        for position in all_menu:
            await safe_send_message(bot, message, text=f"Напиток: {position.title}\nЦена: {position.price} руб.")
            picture = position.picture_path
            try:
                await message.answer_photo(FSInputFile(picture))
            except Exception:
                await safe_send_message(bot, message, text='Изображение не найдено', reply_markup=menu_buttons())
    else:
        await safe_send_message(bot, message, text="Меню не найдено.", reply_markup=menu_buttons())