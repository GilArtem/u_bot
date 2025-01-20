from sqlalchemy import select

from database.models import User, async_session
from errors.errors import *
from handlers.errors import db_error_handler

from .req_user import get_user
from .req_transaction import create_transaction

from instance import logger


@db_error_handler
async def get_user_admin(user_id: int):
    async with async_session() as session:
        user_admin = await session.scalar(select(User).where(User.id == user_id, User.is_superuser == True))
        if user_admin:
            return user_admin
        else:
            return None

@db_error_handler
async def debit_balance(user_id: int, amount: float):
    async with async_session() as session:
        logger.debug(f"Начало списания баланса. user_id={user_id}, amount={amount}")
        user = await get_user(user_id, session=session)
        logger.debug(f"Пользователь: {user}")
        if user:
            if user.balance >= amount:
                user.balance -= amount
                logger.debug(f"Новый баланс: {user.balance}")
                session.add(user)
                await create_transaction(user_id=user_id, event_id=None, amount=amount, transaction_type='списание', session=session)
                await session.commit()
                logger.debug("Транзакция завершена успешно")
                return True
            else:
                logger.debug("Недостаточно средств на балансе")
                await session.rollback()
                return False
        else: 
            logger.debug("Пользователь не найден")
            await session.rollback()
            return None