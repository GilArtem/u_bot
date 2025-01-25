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

def choose_menu_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back"),
             InlineKeyboardButton(text="Вперед", callback_data="forward")]
        ]
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
