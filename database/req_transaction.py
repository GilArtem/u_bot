import datetime

# from database.models import Transaction, 
from database.models import TransactionRequest, async_session
from handlers.errors import db_error_handler

from instance import logger

# @db_error_handler
# async def create_transaction(user_id: int, event_id: int, amount: float, transaction_type: str):
#     async with async_session() as session:
#         new_transaction = Transaction(
#             user_id=user_id,
#             event_id=event_id,
#             amount=amount,
#             date=datetime.datetime.now(),
#             transaction_type=transaction_type 
#         )
#         session.add(new_transaction)
#         logger.info(f"Транзакция создана: user_id={user_id}, type={transaction_type}, amount={amount}")
#         await session.commit()
        

@db_error_handler
async def create_transaction(user_id: int, admin_id: int, amount: float):
    async with async_session() as session:
        transaction_request = TransactionRequest(admin_id=admin_id, user_id=user_id, amount=amount, status='in_process')
        session.add(transaction_request)
        await session.commit()
        logger.info(f"Создана новая транзакция: user_id={user_id}, admin_id={admin_id}, amount={amount}")
        
        




# # Функция для создания записи о транзакции
# @db_error_handler
# async def create_transaction(user_id: int, admin_id: int, amount: float):
#     async with async_session() as session:
#         transaction_request = TransactionRequest(
#             admin_id=admin_id, 
#             user_id=user_id,
#             amount=amount, 
#             status='in_process')
#         session.add(transaction_request)
#         logger.info(f"Транзакция создана: user_id={user_id}, status={transaction_request.status}, amount={amount}")
#         await session.commit()
