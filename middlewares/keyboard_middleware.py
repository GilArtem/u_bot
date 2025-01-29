from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Awaitable, Any

from keyboards.keyboards import user_keyboard, admin_keyboard
from database.req_admin import get_user_admin 

class KeyboardMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]], event: Message, data: Dict[str, Any]
    ) -> Any:
        is_admin = await get_user_admin(event.from_user.id)
        keyboard = admin_keyboard() if is_admin else user_keyboard()

        try:
            await event.edit_text(event.text, reply_markup=keyboard)  
        except Exception:
            pass  

        return await handler(event, data)
