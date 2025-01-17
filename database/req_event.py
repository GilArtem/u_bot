from database.models import Event, Date, async_session
from errors.errors import *
from handlers.errors import db_error_handler

@db_error_handler
async def create_event(title: str, event_date: Date, description: str, menu: str): # menu: byte? 
    async with async_session() as session:
        new_event = Event(
            title=title,
            date=event_date,
            description=description,
            menu=menu
        )
        session.add(new_event)
        await session.commit()
        
        