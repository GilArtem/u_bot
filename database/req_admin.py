from sqlalchemy import select

from database.models import User, async_session
from errors.errors import *
from handlers.errors import db_error_handler


@db_error_handler
async def get_user_admin(user_id: int):
    async with async_session() as session:
        user_admin = await session.scalar(select(User).where(User.id == user_id, User.is_superuser == True))
        if user_admin:
            return user_admin
        else:
            return None


@db_error_handler
async def get_all_users():
    async with async_session() as session:
        pass



@db_error_handler
async def add_new_admin():
    async with async_session() as session:
        pass