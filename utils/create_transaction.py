from database.models import TransactionRequest, async_session


async def create_transaction(user_id: int, admin_id: int, amount: float):
    async with async_session() as session:
        transaction_request = TransactionRequest(admin_id=admin_id, user_id=user_id, amount=amount, status='in_process')
        session.add(transaction_request)
        await session.commit()
        return transaction_request
