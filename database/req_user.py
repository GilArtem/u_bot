from sqlalchemy import select

from database.models import User, async_session
from errors.errors import *
from handlers.errors import db_error_handler


@db_error_handler
async def get_user(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        if user:
            return user
        else:
            return None
    

@db_error_handler
async def create_user(user_id: int, name: str = ""):  
    async with async_session() as session:
        user = await get_user(user_id)
        if not user:
            new_user = User(id=user_id, name=name, balance=0.0, is_superuser=False)
            session.add(new_user)
            await session.commit()
        else:
            raise Error409
        
        
@db_error_handler
async def get_all_users():
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users.all()