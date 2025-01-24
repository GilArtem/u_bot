from sqlalchemy import select
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery 
from aiogram.fsm.context import FSMContext
from database.req_admin import debit_balance, get_user_admin
from database.req_user import get_user 
from utils.create_user import create_user
from database.req_menu import get_all_menu
from database.req_transaction import get_in_process_transaction
from database.models import async_session, TransactionRequest
from handlers.errors import safe_send_message
from handlers.admin import cmd_scan_qr_code
from utils.generate_qr_code import generate_qr_code
from keyboards.keyboards import menu_buttons
from instance import bot

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    hash_value = command.args  # scan_qr_code_user_12345
    
    if hash_value and hash_value.startswith('scan_qr_code_user_'):
        user_admin = await get_user_admin(message.from_user.id)
        if not user_admin:
            await safe_send_message(bot, message, text='У Вас нет прав администратора.')
            return
        
        await cmd_scan_qr_code(message, state, hash_value)
    else:
        user = await get_user(message.from_user.id)
        if not user:
            await create_user(message.from_user.id, message.from_user.username)
        await safe_send_message(bot, message, text="Приветствуем тебя в нашем боте 'U', который станет твоим проводником и помощником на всех ивентах", reply_markup=menu_buttons())



@router.callback_query(F.data.in_(['confirm_user', 'cancel_user', 'cancel_admin']))
async def handle_user_response(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        data = await state.get_data()
        transaction_id = data.get('transaction_id')
        if not transaction_id:
            await callback.message.answer("Транзакция не найдена.")
            return
        
        transaction = await session.get(TransactionRequest, transaction_id)
        if not transaction or transaction.status != 'in_process':
            await callback.message.answer("Транзакция уже завершена или отменена.")
            return
        
        if callback.data == 'confirm_user':
            debit_success = await debit_balance(transaction.user_id, transaction.amount)
            if debit_success:
                transaction.status = 'completed'
                await session.commit()
                await callback.message.answer("Операция подтверждена и завершена.")
                await safe_send_message(bot, transaction.admin_id, text="Пользователь подтвердил операцию.")
                await safe_send_message(bot, transaction.user_id, text=f'С вашего баланса списано {transaction.amount} рублей.')
                await safe_send_message(bot, transaction.admin_id, text='Операция успешно выполнена и подтверждена.')
            else:
                await callback.message.answer("Ошибка: недостаточно средств на балансе.")
                await safe_send_message(bot, transaction.admin_id, text='Ошибка: недостаточно средств на балансе.')
        
        elif callback.data == 'cancel_user':
            transaction.status = 'cancelled'   
            await session.commit()
            await callback.message.answer("Операция отменена пользователем.")
            await safe_send_message(bot, transaction.admin_id, text="Пользователь отменил операцию.")
       
        elif callback.data == 'cancel_admin':
            transaction.status = 'admin_cancelled'   
            await session.commit()
            await callback.message.answer("Операция отменена администратором.")
            await safe_send_message(bot, transaction.user_id, text="Администратор отменил операцию.")
            await safe_send_message(bot, transaction.admin_id, text="Вы отменили операцию.")













# @router.callback_query(F.data.in_(['confirm_user', 'cancel_user']))
# async def handle_user_response(callback: CallbackQuery):   
#     async with async_session() as session:
#         request = await get_in_process_transaction(session, callback.from_user.id)
        
#         if not request:
#             await callback.message.answer("Транзакция уже завершена или отменена.") 
#             return
        
#         if callback.data == 'confirm_user':
#             debit_success = await debit_balance(request.user_id, request.amount)
#             if debit_success:
#                 request.status = 'completed'
#                 await session.commit()
#                 await callback.message.answer("Операция подтверждена и завершена.")
#                 await safe_send_message(bot, request.admin_id, text="Пользователь подтвердил операцию.")
#                 await safe_send_message(bot, request.user_id, text=f'С вашего баланса списано {request.amount} рублей.') 
#                 await safe_send_message(bot, request.admin_id, text='Операция успешно выполнена и подтверждена.')
#             else:
#                 await callback.message.answer("Ошибка: недостаточно средств на балансе.")
#                 await safe_send_message(bot, request.admin_id, text='Ошибка: недостаточно средств на балансе.')
#         elif callback.data == 'cancel_user':
#             request.status = 'cancel'   
#             await session.commit()
#             await callback.message.answer("Операция отменена.")
#             await safe_send_message(bot, request.admin_id, "Пользователь отменил операцию.")
       


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


@router.message(Command('show_menu'))  # Изменить (добавить кнопки перелистования позиций). По одной или по три штуки ?
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