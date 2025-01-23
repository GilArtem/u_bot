from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def menu_buttons():
    keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Меню'), KeyboardButton(text='Показать QR')],
        [KeyboardButton(text='Проверить баланс'), KeyboardButton(text='Пополнить баланс')]
    ],
    resize_keyboard=True
    )
    return keyboard

user_selection_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Подтвердить', callback_data='confirm_user'),
         InlineKeyboardButton(text='Отменить', callback_data='cancel_user')]
    ]
)

admin_selection_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Отменить', callback_data='cancel_admin')]
    ]
)

def confirmation_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Подтвердить', callback_data='confirm_user'),
             InlineKeyboardButton(text='Отклонить', callback_data='cancel_user')]
        ]
    )
    return keyboard

admin_selection_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Отменить', callback_data='cancel_admin')]
    ]
)