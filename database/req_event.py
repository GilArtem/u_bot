from sqlalchemy import select

import datetime
from database.models import Event, Date, async_session
from errors.errors import *
from handlers.errors import db_error_handler

@db_error_handler
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
        
        
@db_error_handler
async def get_event_by_title_and_date(title: str, event_date: datetime.date):  
    async with async_session() as session:
        event = await session.scalar(select(Event).where(Event.title == title, Event.date == event_date))
        return event