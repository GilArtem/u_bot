from aiogram.filters import Command, CommandStart, CommandObject
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from database.req_admin import get_user_admin, debit_balance
from database.req_user import get_user, create_user
from database.req_menu import get_all_menu
from database.req_transaction import get_in_process_transaction
from database.models import async_session
from .states import MenuActions
from handlers.errors import safe_send_message
from handlers.admin import cmd_scan_qr_code
from utils.generate_qr_code import generate_qr_code
from utils.make_short_jwt import validate_short_jwt
from keyboards.keyboards import choose_menu_keyboard, admin_keyboard, user_keyboard
from instance import bot
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


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
            debit_success = await debit_balance(transaction.user_id, transaction.amount)
            if debit_success:
                transaction.status = 'completed'
                await session.commit()
                await callback.message.edit_text("Операция подтверждена и завершена.")
                await safe_send_message(bot, transaction.admin_id, text="Пользователь подтвердил операцию.")
                await safe_send_message(bot, transaction.user_id, text=f'С вашего баланса списано {transaction.amount} рублей.') 
                await safe_send_message(bot, transaction.admin_id, text='Операция успешно выполнена и подтверждена.')
            else:
                await callback.message.edit_text("Ошибка: недостаточно средств на балансе.")
                await safe_send_message(bot, transaction.admin_id, text='Ошибка: недостаточно средств на балансе.')
        elif callback.data == 'cancel_user':
            transaction.status = 'user_cancel'   
            await session.commit()
            await callback.message.edit_text("Операция отменена.")
            await safe_send_message(bot, transaction.admin_id, "Пользователь отменил операцию.")
            
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
    short_token = command.args 
    user_admin = await get_user_admin(message.from_user.id)
    user = await get_user(message.from_user.id)
    
    if short_token:
        try:
            await message.delete()
            user_id = await validate_short_jwt(short_token)
            if not user_admin:
                await safe_send_message(bot, message, text='У Вас нет прав администратора.')
                return
            
            await cmd_scan_qr_code(message, state, user_id)
        except ExpiredSignatureError:
            await safe_send_message(bot, message, text='Срок действия QR-кода истек. Запросите у пользователя сгенерировать новый.', reply_markup=admin_keyboard()) 
            
        except InvalidTokenError:
            await safe_send_message(bot, message, text='Неверный QR-код.')
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
        await message.answer("Главное меню администратора", reply_markup=admin_keyboard())
    else:
        await message.answer("Главное меню пользователя", reply_markup=user_keyboard())


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
    user = await get_user(message.from_user.id)
    pass # Логика выполнения транзакции
   

@router.message(Command('show_qr_code'))
@router.message((F.text.lower() == "показать qr"))
async def cmd_show_qr_code(message: Message):
    user_id = message.from_user.id
    qr_code = await generate_qr_code(user_id)
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
