from aiogram.filters import Command, CommandStart, CommandObject
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import decode_payload
from database.req_admin import get_user_admin, debit_user_balance
from database.req_user import get_user, create_user
from database.req_menu import get_all_menu
from database.req_event import get_all_active_events
from database.req_transaction import get_in_process_transaction
from database.models import async_session
from .states import MenuActions
from handlers.errors import safe_send_message
from handlers.admin import cmd_scan_qr_code, cmd_scan_qr_for_balance_up
from utils.generate_qr_code import generate_qr_code, generate_qr_code_for_balance_up
from keyboards.keyboards import choose_menu_keyboard, admin_keyboard, user_keyboard
from instance import bot
from jwt.exceptions import InvalidTokenError


router = Router()

# КНОПКИ ====================================
@router.callback_query(F.data.in_(['confirm_user', 'cancel_user']))
async def handle_user_response(callback: CallbackQuery):   
    is_admin = False
    async with async_session() as session:
        transaction = await get_in_process_transaction(session, callback.from_user.id, is_admin)
        
        if not transaction:
            await callback.message.edit_text("Транзакция уже завершена или отменена.") 
            return
        
        if callback.data == 'confirm_user':
            debit_success = await debit_user_balance(transaction.user_id, transaction.amount)
            if debit_success:
                transaction.status = 'completed'
                await session.commit()
                await callback.message.edit_text("Операция подтверждена и завершена.")
                await safe_send_message(bot, transaction.admin_id, text="Пользователь подтвердил операцию.", reply_markup=admin_keyboard())
                await safe_send_message(bot, transaction.user_id, text=f'С вашего баланса списано {transaction.amount} рублей.', reply_markup=user_keyboard()) 
                await safe_send_message(bot, transaction.admin_id, text='Операция успешно выполнена и подтверждена.', reply_markup=admin_keyboard())
            else:
                await callback.message.edit_text("Ошибка: недостаточно средств на балансе.")
                await safe_send_message(bot, transaction.admin_id, text='Ошибка: недостаточно средств на балансе.', reply_markup=admin_keyboard())
        elif callback.data == 'cancel_user':
            transaction.status = 'user_cancel'   
            await session.commit()
            await callback.message.edit_text("Операция отменена.")
            await safe_send_message(bot, transaction.admin_id, "Пользователь отменил операцию.", reply_markup=admin_keyboard())
            
@router.callback_query(F.data.in_(['back', 'forward']))
async def navigate_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    all_menu = data.get("menu", [])
    curr_index = data.get('curr_index', 0)

    if not all_menu:
        await callback.message.edit_text("Меню не найдено")
        return

    if callback.data == 'back':
        curr_index = max(curr_index - 1, 0)
    elif callback.data == 'forward':
        curr_index = min(curr_index + 1, len(all_menu) - 1)

    await state.update_data(curr_index=curr_index)
    position = all_menu[curr_index]
    text = f"Напиток: {position.title}\nЦена: {position.price} руб."
    picture = position.picture_path
    first_position = curr_index == 0
    last_position = curr_index == len(all_menu) - 1

    if picture:
        try:
            media = InputMediaPhoto(media=FSInputFile(picture), caption=text)
            await callback.message.edit_media(media=media, reply_markup=choose_menu_keyboard(first_position=first_position, last_position=last_position))
        except Exception:
            await callback.message.edit_caption(text + '\n\nИзображение не найдено.', reply_markup=choose_menu_keyboard(first_position=first_position, last_position=last_position))
    else:
        await callback.message.edit_caption(text + '\n\nФотография отсутствует.', reply_markup=choose_menu_keyboard(first_position=first_position, last_position=last_position))
# КНОПКИ ====================================

@router.message(CommandStart())
@router.message((F.text.lower() == "старт"))
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    payload = command.args 
    user_admin = await get_user_admin(message.from_user.id)
    user = await get_user(message.from_user.id)
    
    if payload:
        try:
            await message.delete()
            
            if not user_admin:
                await safe_send_message(bot, message, text='У Вас нет прав администратора.', reply_markup=user_keyboard())
                return
            
            decoded_payload = decode_payload(payload)
            payloads = decoded_payload.split(':')
            
            if len(payloads) == 1:
                user_id = int(payloads[0])
                await cmd_scan_qr_code(message, state, user_id)
            
            elif len(payloads) == 2:
                user_id, command = payloads
                user_id = int(user_id)
                
                if command == 'balance_up':
                    await cmd_scan_qr_for_balance_up(message, state, user_id)       
            else:
                await safe_send_message(bot, message, text='Неизвестная команда в QR-коде.', reply_markup=admin_keyboard())
        except InvalidTokenError:
            await safe_send_message(bot, message, text='Неверный QR-код.', reply_markup=admin_keyboard())
        return
    
    if user_admin:
        await safe_send_message(bot, message, text="Добро пожаловать, администратор!", reply_markup=admin_keyboard())
    
    if not user:
        await create_user(message.from_user.id, message.from_user.username)
    
    if not user_admin:
        await safe_send_message(bot, message, text="Приветствуем тебя в нашем боте 'U', который станет твоим проводником и помощником на всех ивентах", reply_markup=user_keyboard())


@router.message(Command("commands"))
@router.message((F.text.lower() == "команды"))
async def show_menu(message: Message):
    user_admin = await get_user_admin(message.from_user.id)

    if user_admin:
        await message.answer("Кнопки администратора", reply_markup=admin_keyboard())
    else:
        await message.answer("Кнопки пользователя", reply_markup=user_keyboard())


@router.message(Command('info'))
async def cmd_info(message: Message):
    user_admin = await get_user_admin(message.from_user.id)
    if user_admin:
        await safe_send_message(bot, message, text="Это информация для администратора.", reply_markup=admin_keyboard())
    else:
        await safe_send_message(bot, message, text="Это информация для пользователя.", reply_markup=user_keyboard())
      
        
@router.message(Command('check_balance'))
@router.message((F.text.lower() == "проверить баланс"))
async def cmd_check_balance(message: Message):
    user = await get_user(message.from_user.id) 
    await safe_send_message(bot, message, text = f'Ваш текущий баланс: {user.balance} руб.', reply_markup=user_keyboard())


@router.message(Command('balance_up'))
@router.message((F.text.lower() == "пополнить баланс"))
async def cmd_balance_up(message: Message):
    user_id = message.from_user.id
    qr_code = await generate_qr_code_for_balance_up(bot, user_id)
    await message.answer_photo(photo=qr_code, caption="Внимание: Возврат средств невозможен.\n\nДля пополнения баланса покажите QR-код администратору", reply_markup=user_keyboard())
    
   
@router.message(Command('show_qr_code'))
@router.message((F.text.lower() == "показать qr"))
async def cmd_show_qr_code(message: Message):
    user_id = message.from_user.id
    qr_code = await generate_qr_code(bot, user_id)
    await message.answer_photo(photo=qr_code, caption="Покажите ваш уникальный QR-код администратору", reply_markup=user_keyboard())


@router.message(Command('show_menu'))
@router.message((F.text.lower() == "меню"))
async def cmd_show_menu(message: Message, state: FSMContext):
    all_menu = await get_all_menu()
    if not all_menu:
        await message.answer("Меню не найдено.", reply_markup=user_keyboard())
        return

    await state.update_data(menu=all_menu, curr_index=0)
    position = all_menu[0]
    text = f"Напиток {position.title}\nЦена: {position.price} руб."
    picture = position.picture_path

    try:
        await message.answer_photo(FSInputFile(picture), caption=text, reply_markup=choose_menu_keyboard(first_position=True, last_position=(len(all_menu) == 1)))
    except Exception:
        await message.answer(text + '\n\nИзображение не найдено.', reply_markup=choose_menu_keyboard(first_position=True, last_position=(len(all_menu) == 1)))

    await state.set_state(MenuActions.waiting_curr_position)


@router.message(Command('show_all_active_events'))
@router.message((F.text.lower() == "список ивентов"))
async def cmd_show_all_events(message: Message):
    events = await get_all_active_events()
    
    if not events:
        await safe_send_message(bot, message, text="Нет доступных ивентов.", reply_markup=user_keyboard())
        return
    
    event_list = "\n\n".join([f"{event.title}\n {event.date}\n {event.description}" for event in events])
    await safe_send_message(bot, message, text=f"Список ивентов: \n\n{event_list}", reply_markup=user_keyboard())