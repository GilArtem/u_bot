import os
from sqlalchemy import select
from database.models import Menu, async_session
from errors.errors import *
from handlers.errors import db_error_handler

@db_error_handler
async def get_all_menu():
    async with async_session() as session:
        result = await session.execute(select(Menu))
        all_menu = result.scalars().all()
        return all_menu
    
@db_error_handler
async def save_new_menu(title: str, price: float, picture_path: str):
    async with async_session() as session:
        existing_menu = await session.execute(select(Menu).filter_by(title=title))
        if existing_menu.scalar():
            raise ValueError(f"Напиток с названием '{title}' уже существует.")
        new_menu = Menu(title=title, price=price, picture_path=picture_path)
        session.add(new_menu)
        await session.commit()
 
@db_error_handler
async def delete_menu_item(title: str):
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