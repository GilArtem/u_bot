from aiogram.filters import Command, CommandStart
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.req_user import get_user, create_user

from handlers.errors import safe_send_message
from handlers.admin import cmd_scan_qr_code

from utils.generate_qr_code import generate_qr_code

from instance import bot


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    text = message.text
    if text.startswith('/start scan_qr_code_user_'):
        user_id_srt = text.replace('/start scan_qr_code_user_', '')
        try:
            user_id = int(user_id_srt)
            await cmd_scan_qr_code(message, state, user_id)
        except ValueError:
            await safe_send_message(bot, message, text = 'Неверный формат QR-кода.')
    
    else:
        user = await get_user(message.from_user.id)
        if not user:
            await create_user(message.from_user.id, message.from_user.username)
        await safe_send_message(bot, message, text="Приветствуем тебя в нашем боте 'U', который станет твоим проводником и помощником на всех ивентах")


@router.message(Command('info'))
async def cmd_info(message: Message):
    await safe_send_message(bot, message, text="Оставить тут информацию")


@router.message(Command('check_balance'))
async def cmd_check_balance(message: Message):
    user = await get_user(message.from_user.id) 
    await safe_send_message(bot, message, text = f'Ваш текущий баланс: {user.balance} руб.')


@router.message(Command('balance_up'))
async def cmd_balance_up(message: Message):
    user = await get_user(message.from_user.id)
    pass # Логика выполнения транзакции
   

@router.message(Command('show_qr_code'))
async def cmd_show_qr_code(message: Message):
    user_id = message.from_user.id
    qr_code = generate_qr_code(user_id)
    await message.answer_photo(photo=qr_code, caption="Покажите ваш уникальный QR-код администратору")
