from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database.models import Event, Date, async_session
from errors.errors import *
from handlers.errors import db_error_handler

        
@db_error_handler
async def get_event_by_title(title: str):  
    async with async_session() as session:
        event = await session.scalar(select(Event).where(Event.title == title))
        return event  
    
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
async def get_all_events():
    async with async_session() as session:
        result = await session.execute(select(Event).options(joinedload(Event.menu)).distinct())
        return result.scalars().all()

@db_error_handler
async def delete_event(title: str):
    async with async_session() as session:
        result = await session.execute(select(Event).filter_by(title=title))
        event = result.scalar_one_or_none()
        
        if not event:
            raise ValueError(f'Ивент с названием {title} не найден.')
        
        await session.delete(event)
        await session.commit()