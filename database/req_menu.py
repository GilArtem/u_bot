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
    