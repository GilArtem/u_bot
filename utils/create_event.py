from database.models import Event, Date, async_session
from errors.errors import *


async def create_event(title: str, event_date: Date, description: str, menu_id: str=None): 
    async with async_session() as session:
        new_event = Event(
            title=title,
            date=event_date,
            description=description,
            menu_id=menu_id
        )
        session.add(new_event)
        await session.commit()
        