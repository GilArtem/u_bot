import os
from sqlalchemy import select
from database.models import Menu, async_session
from errors.errors import *
from handlers.errors import db_error_handler
from typing import List

@db_error_handler
async def get_all_menu() -> List[Menu]:
    """ 
    Получение всех записей меню из базы данных.

    Returns:
        List[Menu]: Список объектов всех записей меню.
    """
    async with async_session() as session:
        result = await session.execute(select(Menu))
        all_menu = result.scalars().all()
        return all_menu
    
@db_error_handler
async def save_new_menu(title: str, price: float, picture_path: str) -> None:
    """ 
    Сохранение нового элемента меню в базу данных.

    Args:
        title (str): Название нового элемента меню.
        price (float): Цена нового элемента меню.
        picture_path (str): Путь к изображению нового элемента меню.
    """
    async with async_session() as session:
        existing_menu = await session.execute(select(Menu).filter_by(title=title))
        if existing_menu.scalar():
            raise ValueError(f"Напиток с названием '{title}' уже существует.")
        new_menu = Menu(title=title, price=price, picture_path=picture_path)
        session.add(new_menu)
        await session.commit()
 
@db_error_handler
async def delete_menu_item(title: str) -> None:
    """ 
    Удаление элемента меню по названию.

    Args:
        title (str): Название элемента меню, который нужно удалить.
    """
    async with async_session() as session:
        result = await session.execute(select(Menu).filter_by(title=title))
        menu_item = result.scalar_one_or_none()
        
        if not menu_item:
            raise ValueError(f"Напиток с названием '{title}' не найден.")
        
        picture_path = menu_item.picture_path
        
        await session.delete(menu_item)
        await session.commit()
        
        if picture_path and os.path.exists(picture_path):
            os.remove(picture_path)