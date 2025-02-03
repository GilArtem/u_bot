from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def user_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Меню'), KeyboardButton(text='Показать QR')],
            [KeyboardButton(text='Проверить баланс'), KeyboardButton(text='Пополнить баланс')],
            [KeyboardButton(text='Список ивентов')]
        ],
        resize_keyboard=True
    )
    return keyboard


def admin_keyboard(): 
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Новый ивент'), KeyboardButton(text='Уведомить об ивенте')],
            [KeyboardButton(text='Все ивенты'), KeyboardButton(text='Убрать ивент')],
            [KeyboardButton(text='Добавить в меню'), KeyboardButton(text='Убрать из меню')],
            [KeyboardButton(text='Меню')]
        ],
        resize_keyboard=True
    )
    return keyboard


def user_selection_button():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Подтвердить', callback_data='confirm_user'),
             InlineKeyboardButton(text='Отклонить', callback_data='cancel_user')]
        ]
    )
    return keyboard


def admin_selection_button():
    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Отменить', callback_data='cancel_admin')]
    ]
)
    return keyboard


def admin_cancel():
    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Отменить', callback_data='event_cancel_admin')]
    ]
)
    return keyboard


def choose_menu_keyboard(first_position: bool = False, last_position: bool = False):
    buttons = []
    
    if not first_position:
        buttons.append(InlineKeyboardButton(text="Назад", callback_data='back'))
    if not last_position:
        buttons.append(InlineKeyboardButton(text='Вперед', callback_data='forward'))
        
    return InlineKeyboardMarkup(inline_keyboard=[buttons])