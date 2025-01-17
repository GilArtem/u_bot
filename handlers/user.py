import segno
from io import BytesIO
from aiogram.filters import Command, CommandStart
from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.errors import safe_send_message
from keyboards.keyboards import get_some_kb, get_some_ikb
from instance import bot
from database.req_user import *

router = Router()

class UserActions(StatesGroup):
    pass


@router.message(CommandStart())
async def cmd_start(message: Message):
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
    if user:
        await safe_send_message(bot, message, text = f'Ваш текущий баланс: {user.balance} руб.')
    else:
        await safe_send_message(bot, message, text = 'Пользоватеь не найден.')  # Придумать адекватный вывод для пользователя


@router.message(Command('balance_up'))
async def cmd_balance_up(message: Message):
    user = await get_user(message.from_user.id)
    if user:
        pass # Логика выполнения транзакции
    else:
        await safe_send_message(bot, message, text = 'Пользоватеь не найден.')   # Придумать адекватный вывод для пользователя
    

@router.message(Command('show_qr_code'))
async def cmd_show_qr_code(message: Message):
    user = await get_user(message.from_user.id)
    if user:
        user_id = message.from_user.id
        qr_code = generate_qr_code(user_id)
        await message.answer_photo(photo=qr_code, caption="Покажите ваш уникальный QR-код администратору")
    else:
        await safe_send_message(bot, message, text = 'Пользоватеь не найден.')   # Придумать адекватный вывод для пользователя


# Убрать функционал в отдельную директорию!
def generate_qr_code(user_id: int):
    qr = segno.make(user_id, micro=False)
    
    buffer = BytesIO()
    qr.save(buffer, kind='png', scale=10, dark='black', light='white')
    buffer.seek(0)
    
    return BufferedInputFile(buffer.getvalue(), filename="qr_code.png")























# @router.message(F.text.contains("ss"))
# async def ss_contains(message: Message):
#     await safe_send_message(bot, message, text="Это обработчик сообщения, которое содержит 'ss'")


# @router.message(Command('kb_ex'))
# async def cmd_kb_ex(message: Message):
#     await safe_send_message(bot, message, text='Это пример reply keyboard\nВсе кнопки отпраляются боту как сообщения',
#                             reply_markup=get_some_kb())


# @router.message(Command('ikb_ex'))
# async def cmd_ikb_ex(message: Message):
#     await safe_send_message(bot, message, text='Это пример inline keyboard\nВсе кнопки отпралвяются боту как '
#                                                'callback_data', reply_markup=get_some_ikb())


# @router.callback_query(F.data == "f_btn")
# async def callback_data_ex1(callback: CallbackQuery):
#     await safe_send_message(bot, callback, text='Это сообщение после нажатие на первую кнопку')
#     await callback.answer()


# @router.callback_query(F.data == "s_btn")
# async def callback_data_ex1(callback: CallbackQuery):
#     await safe_send_message(bot, callback, text='Это сообщение после нажатие на вторую кнопку')
#     await callback.answer()


# @router.callback_query(F.data == "t_btn")
# async def callback_data_ex1(callback: CallbackQuery):
#     await safe_send_message(bot, callback, text='Это сообщение после нажатие на третью кнопку')
#     await callback.answer()


# class ExState(StatesGroup):
#     first_mes = State()
#     second_mes = State()


# @router.message(Command('state_ex'))
# async def state_ex_begin(message: Message, state: FSMContext):
#     await safe_send_message(bot, message, text='Это пример использования состояний\nЗагадай число')
#     await state.set_state(ExState.first_mes)


# @router.message(ExState.first_mes)
# async def state_ex_mid(message: Message, state: FSMContext):
#     await safe_send_message(bot, message, text='Теперь я тасую числа и пытаюсь тебя запутать\nЗагадай букву')
#     await state.set_data({'numb': message.text})
#     await state.set_state(ExState.second_mes)


# @router.message(ExState.second_mes)
# async def state_ex_end(message: Message, state: FSMContext):
#     data = await state.get_data()
#     numb = data.get('numb')
#     await safe_send_message(bot, message, text=f'Твое число - {numb}')
#     await state.clear()