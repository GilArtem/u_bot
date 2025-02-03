import os
from uuid import uuid4
from dotenv import load_dotenv
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import Command 
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.req_admin import get_user_admin, update_user_balance
from database.req_event import get_event_by_title, create_event, get_all_events, delete_event
from database.req_transaction import update_transaction_status, get_in_process_transaction, create_debit_transaction, create_balance_up_transaction
from database.req_user import get_user
from database.req_menu import save_new_menu, delete_menu_item
from database.models import async_session 
from handlers.states import AdminActions, EventActions, MenuActions
from handlers.errors import safe_send_message
from keyboards.keyboards import user_selection_button, admin_cancel, admin_keyboard, user_keyboard, admin_selection_button
from utils.notify_all_users import notify_all_users
from instance import bot

router = Router()
load_dotenv()


# КНОПКИ ====================================
@router.callback_query(F.data.in_(['cancel_admin']))
async def handle_admin_responce(callback: CallbackQuery) -> None:
    """ 
    Обработка запроса отмены транзакции администратором.

    Args:
        callback (CallbackQuery): Объект callback-запроса от Telegram.
    """
    is_admin = True
    user_id = callback.from_user.id

    async with async_session() as session:
        transaction = await get_in_process_transaction(session, user_id, is_admin)
        if not transaction:
            await callback.message.edit_text("Активной транзакции не найдено.")
            return

        await update_transaction_status(transaction.id, 'admin_cancel')

        await callback.message.edit_text("Транзакция успешно отменена.")
        target_id = transaction.user_id if is_admin else transaction.admin_id
        await safe_send_message(bot, target_id, text="Транзакция была отменена.")
   
   
@router.callback_query(F.data == 'event_cancel_admin')
async def cancel_operation(callback: CallbackQuery, state: FSMContext) -> None:
    """ 
    Отмена любой текущей операции администратора.
    
    Args:
        callback (CallbackQuery): Объект callback-запроса от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    await state.clear()
    await callback.message.edit_text("Операция была отменена.")
# КНОПКИ ====================================    


@router.message(Command('scan_qr_code'))
async def cmd_scan_qr_code(message: Message, state: FSMContext, user_id: int) -> None:
    """ 
    Обработка команды `/scan_qr_code`, которая запускает процесс списания средств у пользователя.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
        user_id (int): Идентификатор пользователя, для которого будет выполнено списание.
    """
    user_admin = await get_user_admin(message.from_user.id) 
    if not user_admin:
        await safe_send_message(bot, message, text='У Вас нет прав администратора.', reply_markup=user_keyboard())
        return 
    
    user = await get_user(user_id)
    if not user:
        await safe_send_message(bot, message, text='Пользователь не найден.', reply_markup=admin_keyboard())
        return
    
    async with async_session() as session:
        transaction = await get_in_process_transaction(session, user_id, is_admin=False)
        if transaction:
            await update_transaction_status(transaction.id, 'expired')  
            await safe_send_message(bot, message, text='Предыдущая транзакция была отклонена, так как вы начали новую.')
            await safe_send_message(bot, user_id, text="Предыдущая транзакция была отклонена, так как началась новая.")
                
    await safe_send_message(bot, message, text=f"Информация о пользователе:\nИмя: {user.name}\nБаланс: {user.balance}")
    await safe_send_message(bot, message, text='Введите сумму списания:', reply_markup=admin_cancel())
    await state.update_data(user_id=user_id, admin_id=message.from_user.id)
    await state.set_state(AdminActions.waiting_input_amount)

@router.message(AdminActions.waiting_input_amount)
async def debit_amount_chosen(message: Message, state: FSMContext) -> None:
    """ 
    Обработка введенной администратором суммы списания.

    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    if message.text.lower() == 'отменить':
        await cancel_operation(message, state)
        return 
    
    try:
        amount = float(message.text)
        if amount <= 0:
            await safe_send_message(bot, message, text='Сумма должна быть больше нуля.', reply_markup=admin_keyboard())
            return
    except ValueError:
        await safe_send_message(bot, message, text='Неверный формат суммы. Введите число.', reply_markup=admin_keyboard())
        return 
    
    data = await state.get_data()
    user_id = data.get('user_id')
    admin_id = data.get('admin_id')
    user = await get_user(user_id)
    
    if not user:
        await safe_send_message(bot, message, text='Пользователь не найден.', reply_markup=admin_keyboard())
        await state.clear()
        return
    
    if user.balance >= amount:  
        await safe_send_message(bot, user_id, text='Внимание: Возврат средств обратно на счет невозможен!', reply_markup=user_keyboard())
        await safe_send_message(bot, user_id, text=f'Администратор запросил списание {amount} рублей.\nПодтвердите операцию?', reply_markup=user_selection_button())
        transaction = await create_debit_transaction(user_id, admin_id, amount)  
        if transaction:
            await state.update_data(transaction_id=transaction.id) 
            await safe_send_message(bot, message, text=f'Запрос на списание {amount} рублей отправлен пользователю.', reply_markup=admin_selection_button())
        else:
            await safe_send_message(bot, message, text='Ошибка при создании транзакции.', reply_markup=admin_keyboard())
            await state.clear()
    else:
        await safe_send_message(bot, message, text='Недостаточно средств на балансе.', reply_markup=admin_keyboard())
        await safe_send_message(bot, user_id, text='У Вас недостачно средств. Пополните баланс для осуществления покупки.', reply_markup=user_keyboard())
        await state.clear()

    await state.clear()

@router.message(Command('cmd_scan_qr_for_balance_up'))
async def cmd_scan_qr_for_balance_up(message: Message, state: FSMContext, user_id: int) -> None:
    """ 
    Обработка команды `/cmd_scan_qr_for_balance_up`, которая запускает процесс пополнения средств пользователя.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
        user_id (int): Идентификатор пользователя, для которого будет выполнена операция.
    """
    user_admin = await get_user_admin(message.from_user.id)
    if not user_admin:
        await safe_send_message(bot, message, text='У Вас нет прав администратора.', reply_markup=user_keyboard())
        return
    
    user = await get_user(user_id)
    if not user:
        await safe_send_message(bot, message, text='Пользователь не найден.', reply_markup=admin_keyboard())
        return
            
    await safe_send_message(bot, message, text=f"Информация о пользователе:\nИмя: {user.name}\nБаланс: {user.balance}")
    await safe_send_message(bot, message, text='Введите сумму для пополнения баланса:', reply_markup=admin_cancel())
    await state.update_data(user_id=user_id, admin_id=message.from_user.id)
    await state.set_state(AdminActions.waiting_input_balance_up_amount)
    
@router.message(AdminActions.waiting_input_balance_up_amount)
async def balance_up_amount_choose(message: Message, state: FSMContext) -> None:
    """ 
    Обработка введенной администратором суммы пополнения.

    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    if message.text.lower() == 'отменить':
        await cancel_operation(message, state)
        return
        
    try:
        amount = float(message.text)
        if amount <= 0:
            await safe_send_message(bot, message, text='Сумма должна быть больше нуля.', reply_markup=admin_keyboard())
            return
    except ValueError:
        await safe_send_message(bot, message, text="Неверный формат суммы. Введите число.", reply_markup=admin_keyboard())
        return
        
    data = await state.get_data()
    user_id = data.get('user_id')
    admin_id = data.get('admin_id')
    user = await get_user(user_id)
    
    if not user:
        await safe_send_message(bot, message, text='Пользователь не найден.', reply_markup=admin_keyboard())
        await state.clear()
        return
        
    transaction = await create_balance_up_transaction(user_id, admin_id, amount)
    if transaction:
        user.balance += amount
        await update_user_balance(user_id, user.balance)
        await safe_send_message(bot, message, text=f'Баланс пользователя {user.name} успешно пополнен на {amount} рублей.', reply_markup=admin_keyboard())
        await safe_send_message(bot, user_id, text=f"Ваш баланс пополнен на {amount}руб.", reply_markup=user_keyboard())
    else:
        await safe_send_message(bot, message, text='Ошибка при создании транзакции.', reply_markup=admin_keyboard())

    await state.clear()


@router.message(Command('new_event'))
@router.message((F.text.lower() == "новый ивент"))
async def cmd_new_event(message: Message, state: FSMContext) -> None:
    """ 
    Обработка команды `/new_event` или текста "новый ивент", которая запускает процесс создания нового события.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    user_admin = await get_user_admin(message.from_user.id)
    if not user_admin:
        await safe_send_message(bot, message, text = 'У Вас нет прав администратора.', reply_markup=user_keyboard())
        return
    
    await safe_send_message(bot, message, text = 'Введите название нового ивента:', reply_markup=admin_cancel())
    await state.set_state(AdminActions.waiting_title)
    
@router.message(AdminActions.waiting_title)
async def title_chosen(message: Message, state: FSMContext) -> None:
    """ 
    Обработка введенного названия события.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """    
    title = message.text
    event = await get_event_by_title(title)
    
    if title.lower() == "отменить":
        await cancel_operation(message, state)
        return 
    
    if not event:
        await state.update_data(title=message.text)
        await safe_send_message(bot, message, text = 'Введите дату проведения ивента (формат ГГГГ-ММ-ДД):', reply_markup=admin_cancel())
        await state.set_state(AdminActions.waiting_date)
    else:
        await safe_send_message(bot, message, text=f"Ивент с названием {title} уже существет. Введите другое название:", reply_markup=admin_cancel())
        await state.set_state(AdminActions.waiting_title)
        
@router.message(AdminActions.waiting_date)
async def date_chosen(message: Message, state: FSMContext) -> None:
    """ 
    Обработка введенной даты проведения события.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    if message.text.lower() == "отменить":
        await cancel_operation(message, state)
        return 
    
    try:
        event_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        await state.update_data(date=event_date)
        await safe_send_message(bot, message, text = 'Введите описание ивента:', reply_markup=admin_cancel())
        await state.set_state(AdminActions.waiting_description)
    except ValueError:
        await safe_send_message(bot, message, text = "Неверный формат даты. Введите данные формата: ГГГГ-ММ-ДД.", reply_markup=admin_cancel())

@router.message(AdminActions.waiting_description)
async def description_chosen(message: Message, state: FSMContext) -> None:
    """ 
    Обработка введенного описания события.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    if message.text.lower() == "отменить":
        await cancel_operation(message, state)
        return 
    
    data = await state.get_data()
    event_title = data['title']
    event_date = data['date']
    event_description = message.text
    menu_id = None
    
    await create_event(event_title, event_date, event_description, menu_id)
    await safe_send_message(bot, message, text = f'Ивент: {event_title}.\nДата проведения: {event_date}.\nОписание:\n\n{event_description}.', reply_markup=admin_keyboard())
    await state.clear()


@router.message(Command('send_event_to_users'))
@router.message((F.text.lower() == "уведомить об ивенте"))
async def cmd_send_event_to_users(message: Message, state: FSMContext) -> None:
    """ 
    Запуск процесса отправки уведомлений о событии пользователям.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    user_admin = await get_user_admin(message.from_user.id)
    if user_admin:
        await state.set_state(EventActions.waiting_event_title)
        await safe_send_message(bot, message, text = "Введите название ивента:", reply_markup=admin_cancel())  # TODO 2 Попробуй получить все ивенты и вывести клаиатуру (может быть какую-нибудь классификацию для оконченных и действующих ивентов)
    else:
        await safe_send_message(bot, message, text = 'У Вас нет прав администратора.', reply_markup=user_keyboard()) 
        
@router.message(EventActions.waiting_event_title)
async def title_event_chosen(message: Message, state: FSMContext) -> None:
    """ 
    Обработка введенного названия события.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    title = message.text
    event = await get_event_by_title(title)
    
    if title.lower() == "отменить":
        await cancel_operation(message, state)
        return 
    
    if event:
        await notify_all_users(event.title, event.date, event.description)
        await safe_send_message(bot, message, text='Информация о ивенте передана пользователям.', reply_markup=admin_keyboard())
        await state.clear()
    else:
        await safe_send_message(bot, message, text="Ивент с данным названием не найден. Попробуйте еще раз.", reply_markup=admin_cancel())
        

@router.message(Command('add_menu'))
@router.message(F.text.lower() == "добавить в меню")
async def cmd_add_menu(message: Message, state: FSMContext) -> None:
    """ 
    Запуск процесса добавления нового элемента в меню.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    user_admin = await get_user_admin(message.from_user.id)
    if not user_admin:
        await safe_send_message(bot, message, text = 'У Вас нет прав администратора.', reply_markup=user_keyboard())
        return
    await safe_send_message(bot, message, text="Введите название напитка:", reply_markup=admin_cancel())
    await state.set_state(MenuActions.waiting_title)
    
@router.message(MenuActions.waiting_title)
async def title_menu_choose(message: Message, state: FSMContext) -> None:
    """ 
    Обработка введенного названия нового элемента меню.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    title = message.text
    if title.lower() == "отменить":
        await cancel_operation(message, state)
        return 
    
    await state.update_data(title=message.text)
    await safe_send_message(bot, message, text='Укажите цену напитка:', reply_markup=admin_cancel())
    await state.set_state(MenuActions.waiting_price)
    
@router.message(MenuActions.waiting_price)
async def price_menu_choose(message: Message, state: FSMContext) -> None:
    """ 
    Обработка введенной цены нового элемента меню.
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    if message.text.lower() == 'отменить':
        await cancel_operation(message, state)
        return 
    
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
        await state.update_data(price=price)
        await safe_send_message(bot, message, text='Отправьте фотографию напитка:', reply_markup=admin_cancel()) 
        await state.set_state(MenuActions.waiting_picture)
    except ValueError:
        await safe_send_message(bot, message, text='Цена должна быть положительным числом. Попробуйте еще раз:', reply_markup=admin_cancel())
        
@router.message(MenuActions.waiting_picture, F.photo)
async def picture_choose(message: Message, state: FSMContext, bot: Bot) -> None:
    """ 
    Обработка отправленной фотографии нового элемента меню.
    
    Args: 
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
        bot (Bot): Экземпляр бота для работы с файлами.
    """
    # Создаем директорию для хранения изображений если ее нет 
    UPLOAD_DIR = os.getenv('UPLOAD_DIR')
    os.makedirs(UPLOAD_DIR, exist_ok=True) 
    
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    filename = f"{uuid4().hex}.jpg"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    await bot.download_file(file_info.file_path, destination=file_path)
    
    data = await state.get_data()
    title = data.get('title')
    price = data.get('price')    

    await save_new_menu(title, price, file_path) 
    await safe_send_message(bot, message, text=f"Напиток '{title}' добавлен в меню.", reply_markup=admin_keyboard())
    await state.clear()


@router.message(Command('delete_menu'))
@router.message((F.text.lower() == "убрать из меню"))
async def cmd_delete_menu(message: Message, state: FSMContext) -> None:
    """ 
    Запуск процесса удаления элемента из меню.
    
    Args: 
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    user_admin = await get_user_admin(message.from_user.id)
    if not user_admin:
        await safe_send_message(bot, message, text = 'У Вас нет прав администратора.', reply_markup=user_keyboard())
        return
    await safe_send_message(bot, message, text="Введите название напитка для удаления:", reply_markup=admin_cancel())
    await state.set_state(MenuActions.waiting_title_for_delete)

@router.message(MenuActions.waiting_title_for_delete)
async def title_menu_delete_choose(message: Message, state: FSMContext) -> None:
    """ 
    Обработка введенного названия элемента меню для удаления.
    
    Args: 
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    title = message.text
    if title.lower() == "отменить":
        await cancel_operation(message, state)
        return

    try:
        await delete_menu_item(title)
        await safe_send_message(bot, message, text=f"Напиток '{title}' успешно удален из меню.", reply_markup=admin_keyboard())
    except ValueError as e:
        await safe_send_message(bot, message, text=f'{str(e)}', reply_markup=admin_keyboard())
    except Exception as e:
        await safe_send_message(bot, message, text=f'Произошла ошибка при удалении: {e}', reply_markup=admin_keyboard())
    finally:
        await state.clear()
        

@router.message(Command('show_all_events'))
@router.message((F.text.lower() == "все ивенты"))
async def cmd_show_all_events(message: Message) -> None:
    """ 
    Вывод списка всех событий.
    
    Args:
        message (Message): Объект сообщения от Telegram.
    """
    user_admin = await get_user_admin(message.from_user.id)
    if not user_admin:
        await safe_send_message(bot, message, text = 'У Вас нет прав администратора.', reply_markup=user_keyboard())
        return
    
    events = await get_all_events()
    
    if not events:
        await safe_send_message(bot, message, text="Нет доступных ивентов.", reply_markup=admin_keyboard())
        return
    
    event_list = "\n\n".join([f"{event.title}\n {event.date}\n {event.description}" for event in events])
    await safe_send_message(bot, message, text=f"Список ивентов: \n\n{event_list}", reply_markup=admin_keyboard())
   
    
@router.message(Command('delete_event'))
@router.message((F.text.lower() == "убрать ивент"))
async def cmd_show_all_events(message: Message, state: FSMContext) -> None:
    """ 
    Запуск процесса удаления события.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    user_admin = await get_user_admin(message.from_user.id)
    if not user_admin:
        await safe_send_message(bot, message, text = 'У Вас нет прав администратора.', reply_markup=user_keyboard())
        return
    await safe_send_message(bot, message, text='Введите название ивента для удаления:', reply_markup=admin_cancel())
    await state.set_state(EventActions.waiting_title_for_delete_event)
    
@router.message(EventActions.waiting_title_for_delete_event)
async def title_event_for_delete_choose(message: Message, state: FSMContext) -> None:
    """ 
    Обработка введенного названия события для удаления.
    
    Args:
        message (Message): Объект сообщения от Telegram.
        state (FSMContext): Контекст состояния для управления FSM.
    """
    title = message.text
    if title.lower() == 'отменить':
        await cancel_operation(message, state)
        return
    
    try:
        await delete_event(title)
        await safe_send_message(bot, message, text=f"Ивент {title} был успешно удален.", reply_markup=admin_keyboard())
    except ValueError as e:
        await safe_send_message(bot, message, text=f'{str(e)}', reply_markup=admin_keyboard())
    except Exception as e:
        await safe_send_message(bot, message, text=f"Ошибка произошла при удалении: {e}", reply_markup=admin_keyboard())        
    finally:
        await state.clear()