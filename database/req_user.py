from sqlalchemy import select
from database.models import User, async_session
from errors.errors import *
from handlers.errors import db_error_handler


@db_error_handler
async def get_user(user_id: int):
    async with async_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        if user:
            return user.scalars().first()

        else:
            return None

                
@db_error_handler
async def get_all_users():
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users.all()