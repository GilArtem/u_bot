from sqlalchemy import select, and_

from database.models import User, async_session
from errors.errors import *
from handlers.errors import db_error_handler

from .req_user import get_user
from .req_transaction import create_transaction

from instance import logger


# @db_error_handler
# async def get_user_admin(user_id: int):
#     async with async_session() as session:
#         user_admin = await session.scalar(select(User).where(User.id == user_id, User.is_superuser == True))
#         if user_admin:
#             return user_admin
#         else:
#             return None

# @db_error_handler
# async def get_user_admin(user_id: int, is_superuser: bool):
#     async with async_session() as session:
#         row = await session.scalar(select(User).where(and_(
#             User.id == user_id,
#             User.is_superuser == is_superuser)))
#         if row:
#             return row
#         else:
#             return 'not get_user_admin'

@db_error_handler
async def get_user_admin(user_id: int):
    async with async_session() as session:
        user_admin = await session.scalar(select(User).where(and_(User.id == user_id, User.is_superuser == True)))
        if user_admin:
            return user_admin
        else:
            return 'not get_user_admin'

# database/req_admin.py
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




























# @db_error_handler
# async def debit_balance(user_id: int, amount: float):
#     async with async_session() as session:
#         logger.info(f"Начало списания баланса. user_id={user_id}, amount={amount}")
#         try:
#             user = await get_user(user_id)
            
#             if not user:
#                 logger.error("Пользователь не найден")
#                 return None
            
#             if user.balance < amount:
#                 logger.warning(f"Недостаточно средств: баланс={user.balance}, amount={amount}")
#                 return False
            
            
#             user.balance -= amount    
#             session.add(user)
            
            
#             await create_transaction(user_id=user_id, event_id=None, amount=amount, transaction_type='списание')
                
#             await session.commit()
#             logger.info(f"Списание успешно выполнено: user_id={user_id}, amount={amount}")
#             return True
        
#         except Exception as e:
#             logger.error(f"Ошибка при списании баланса: {e}")
#             await session.rollback()
#             raise
        
        
        

# @db_error_handler
# async def debit_balance(user_id: int, amount: float):
#     async with async_session() as session:
#         logger.debug(f"Начало списания баланса. user_id={user_id}, amount={amount}")
#         user = await get_user(user_id)
#         logger.debug(f"Пользователь: {user}")
#         if user:
#             if user.balance >= amount:
#                 user.balance -= amount
#                 logger.debug(f"Новый баланс: {user.balance}")
#                 session.add(user)
#                 await create_transaction(user_id=user_id, event_id=None, amount=amount, transaction_type='списание')
#                 await session.commit()
#                 logger.debug("Транзакция завершена успешно")
#                 return True
#             else:
#                 logger.debug("Недостаточно средств на балансе")
#                 await session.rollback()
#                 return False
#         else: 
#             logger.debug("Пользователь не найден")
#             await session.rollback()
#             return None