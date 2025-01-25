from sqlalchemy import select
from database.models import TransactionRequest, async_session, AsyncSession
from handlers.errors import *


@db_error_handler
async def get_in_process_transaction(session: AsyncSession, user_id: int, is_admin: bool):
    condition = (TransactionRequest.admin_id == user_id if is_admin else TransactionRequest.user_id == user_id)
    transaction_request = await session.execute(select(TransactionRequest)
                          .where(condition, TransactionRequest.status == 'in_process')
                          .order_by(TransactionRequest.created_at.desc())
                          .limit(1)
    )
    return transaction_request.scalar_one_or_none()
 
 
@db_error_handler
async def update_transaction_status(transaction_id: int, new_status: str):
    async with async_session() as session:
        transaction_request = await session.get(TransactionRequest, transaction_id)
        if transaction_request:
            transaction_request.status = new_status
            await session.commit()
        else:
            raise Error404

@db_error_handler
async def create_transaction(user_id: int, admin_id: int, amount: float):
    async with async_session() as session:
        transaction_request = TransactionRequest(admin_id=admin_id, user_id=user_id, amount=amount, status='in_process')
        session.add(transaction_request)
        await session.commit()
        return transaction_request