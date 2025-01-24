from datetime import datetime
from database.req_user import get_all_users
from handlers.errors import safe_send_message
from instance import bot


async def notify_all_users(title: str, event_date: datetime.date, description: str):
    users = await get_all_users()
    for user in users:
        await safe_send_message(bot, user.id, text=f"Новый ивент: {title}\nДата: {event_date}\nОписание: {description}")

