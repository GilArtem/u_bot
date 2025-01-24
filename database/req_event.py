from sqlalchemy import select
import datetime
from database.models import Event, async_session
from errors.errors import *
from handlers.errors import db_error_handler
        
@db_error_handler
async def get_event_by_title_and_date(title: str, event_date: datetime.date):  
    async with async_session() as session:
        event = await session.scalar(select(Event).where(Event.title == title, Event.date == event_date))
        return event