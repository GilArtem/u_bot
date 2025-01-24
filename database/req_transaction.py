from sqlalchemy import select
from database.models import TransactionRequest, async_session, AsyncSession
from handlers.errors import *


@db_error_handler     
async def get_in_process_transaction(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(TransactionRequest).where(
            TransactionRequest.user_id == user_id,
            TransactionRequest.status == 'in_process',
        ).order_by(TransactionRequest.created_at.desc()).limit(1)
    )
    transaction_request = result.scalar_one_or_none()
    return transaction_request
   
 
@db_error_handler
async def update_transaction_status(transaction_id: int, new_status: str):
    async with async_session() as session:
        transaction_request = await session.get(TransactionRequest, transaction_id)
        if transaction_request:
            transaction_request.status = new_status
            await session.commit()
        else:
            raise Error404
