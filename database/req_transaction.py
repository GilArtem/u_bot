from sqlalchemy import select
from database.models import TransactionRequest, async_session, AsyncSession
from handlers.errors import *
from typing import Optional

@db_error_handler
async def get_in_process_transaction(session: AsyncSession, user_id: int, is_admin: bool) -> Optional[TransactionRequest]:
    """ 
    Получение транзакции со статусом 'in_process' для пользователя или администратора.

    Args:
        session (AsyncSession): Активная сессия базы данных.
        user_id (int): Идентификатор пользователя или администратора.
        is_admin (bool): Флаг, указывающий, является ли запрос от администратора (`True`) или пользователя (`False`).

    Returns:
        Optional[TransactionRequest]: Объект транзакции со статусом 'in_process', если такая транзакция существует. 
        Если транзакция не найдена, возвращает `None`.

    """
    condition = (TransactionRequest.admin_id == user_id if is_admin else TransactionRequest.user_id == user_id)
    transaction_request = await session.execute(select(TransactionRequest)
                          .where(condition, TransactionRequest.status == 'in_process')
                          .order_by(TransactionRequest.created_at.desc())
                          .limit(1)
    )
    return transaction_request.scalar_one_or_none()
 
 
@db_error_handler
async def update_transaction_status(transaction_id: int, new_status: str) -> None:
    """ 
    Обновление статуса транзакции.

    Args:
        transaction_id (int): Идентификатор транзакции, которую нужно обновить.
        new_status (str): Новый статус транзакции.
    """
    async with async_session() as session:
        transaction_request = await session.get(TransactionRequest, transaction_id)
        if transaction_request:
            transaction_request.status = new_status
            await session.commit()
        else:
            raise Error404


@db_error_handler
async def create_debit_transaction(user_id: int, admin_id: int, amount: float) -> TransactionRequest:
    """ 
    Создание новой транзакции списания ('debit').

    Args:
        user_id (int): Идентификатор пользователя, для которого создается транзакция.
        admin_id (int): Идентификатор администратора, создавшего транзакцию.
        amount (float): Сумма транзакции.

    Returns:
        TransactionRequest: Созданный объект транзакции.
    """
    async with async_session() as session:
        transaction_request = TransactionRequest(admin_id=admin_id, user_id=user_id, amount=amount, status='in_process', operation_type='debit')
        session.add(transaction_request)
        await session.commit()
        return transaction_request
    
    
@db_error_handler
async def create_balance_up_transaction(user_id: int, admin_id: int, amount: float) -> TransactionRequest:
    """ 
    Создание новой транзакции пополнения счета ('balance_up').
    
    Args:
        user_id (int): Идентификатор пользователя, для которого создается транзакция.
        admin_id (int): Идентификатор администратора, создавшего транзакцию.
        amount (float): Сумма транзакции.

    Returns:
        TransactionRequest: Созданный объект транзакции.
    
    """
    async with async_session() as session:
        transaction_request = TransactionRequest(admin_id=admin_id, user_id=user_id, amount=amount, status='completed',  operation_type='balance_up' )
        session.add(transaction_request)
        await session.commit()
        return transaction_request