from sqlalchemy import select, and_
from database.models import User, async_session
from errors.errors import *
from handlers.errors import db_error_handler


@db_error_handler
async def debit_balance(user_id: int, amount: float) -> bool:
    async with async_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()
        if user and user.balance >= amount:
            user.balance -= amount
            await session.commit()
            return True
        else:
            return False


@db_error_handler
async def get_user_admin(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id, User.is_superuser == True)
        )
        user_admin = result.scalar_one_or_none()
        return user_admin