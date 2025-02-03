from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database.models import Event, Date, async_session
from errors.errors import *
from handlers.errors import db_error_handler
from datetime import date

        
@db_error_handler
async def get_event_by_title(title: str) -> Optional[Event]:  
    """ 
    Получение события по его названию.

    Args:
        title (str): Название события, которое нужно найти.

    Returns:
        Optional[Event]: Объект события (класс `Event`), если событие найдено.
                         Если событие не найдено, возвращает `None`.
    """
    async with async_session() as session:
        event = await session.scalar(select(Event).where(Event.title == title))
        return event  
    
@db_error_handler
async def create_event(title: str, event_date: Date, description: str, menu_id: str=None) -> Event: 
    """ 
    Cоздание нового события.

    Args:
        title (str): Название события.
        event_date (date): Дата проведения события.
        description (str): Описание события.
        menu_id (Optional[int]): Идентификатор меню, связанного с событием. По умолчанию `None`.

    Returns:
        Event: Созданный объект события.
    """
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
async def get_all_events() -> List[Event]:
    """ 
    Получение всех событий из базы данных.

    Returns:
        List[Event]: Список всех событий, отсортированных по дате.
    """
    async with async_session() as session:
        result = await session.execute(select(Event).options(joinedload(Event.menu))
                                       .order_by(Event.date.asc())
                                       .distinct())
        return result.scalars().all()

@db_error_handler
async def delete_event(title: str) -> None:
    """ 
    Удаление события по его названию.

    Args:
        title (str): Название события, которое нужно удалить.
    """
    async with async_session() as session:
        result = await session.execute(select(Event).filter_by(title=title))
        event = result.scalar_one_or_none()
        
        if not event:
            raise ValueError(f'Ивент с названием {title} не найден.')
        
        await session.delete(event)
        await session.commit()
        
@db_error_handler
async def get_all_active_events() -> List[Event]:
    """ 
    Получение всех активных событий (дата >= текущая дата).

    Returns:
        List[Event]: Список активных событий, отсортированных по дате.
    """
    async with async_session() as session:
        curr_date = date.today()
        result = await session.execute(select(Event).options(joinedload(Event.menu))
                              .where(Event.date >= curr_date)
                              .order_by(Event.date.asc())
                              .distinct())
        return result.scalars().all()