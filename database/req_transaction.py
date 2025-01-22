import datetime

from database.models import Transaction, async_session
from handlers.errors import db_error_handler

from instance import logger

@db_error_handler
async def create_transaction(user_id: int, event_id: int, amount: float, transaction_type: str):
    async with async_session() as session:
        new_transaction = Transaction(
            user_id=user_id,
            event_id=event_id,
            amount=amount,
            date=datetime.datetime.now(),
            transaction_type=transaction_type 
        )
        session.add(new_transaction)
        logger.info(f"Транзакция создана: user_id={user_id}, type={transaction_type}, amount={amount}")
        await session.commit()
        
