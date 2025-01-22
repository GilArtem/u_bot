from aiogram.filters import Command, CommandStart, CommandObject
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from database.req_user import get_user, create_user
from database.req_menu import get_all_menu

from handlers.errors import safe_send_message
from handlers.admin import cmd_scan_qr_code

from utils.generate_qr_code import generate_qr_code

from keyboards.keyboards import menu_buttons, user_selection_button

from instance import bot


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    hash_value = command.args #scan_qr_code_user_12345
    if hash_value:
        parts = hash_value.split('_')
        user_id = int(parts[-1])
        await cmd_scan_qr_code(message, state, user_id)
        
    else:
        user = await get_user(message.from_user.id)
        if not user:
            await create_user(message.from_user.id, message.from_user.username)
        
    await safe_send_message(bot, message, text="Приветствуем тебя в нашем боте 'U', который станет твоим проводником и помощником на всех ивентах", reply_markup=menu_buttons())
    

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