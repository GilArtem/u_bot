from sqlalchemy import select
from database.models import User, async_session
from errors.errors import *
from handlers.errors import db_error_handler
from typing import Optional, List


@db_error_handler
async def get_user(user_id: int) -> Optional[User]:
    """ 
    Получение пользователя по идентификатору.

    Args:
        user_id (int): Идентификатор пользователя, которого нужно найти.

    Returns:
        Optional[User]: Объект пользователя, если пользователь найден.
                        Если пользователь не найден, возвращает `None`.
    """
    async with async_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        if user:
            return user.scalars().first()

        else:
            return None

                
@db_error_handler
async def get_all_users() -> List[User]:
    """ 
    Получение всех пользователей из базы данных.

    Returns:
        List[User]: Список объектов пользователей.
    """
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users.all()
    

@db_error_handler
async def create_user(user_id: int, name: str = ""): 
    """ 
    Создание нового пользователя.

    Args:
        user_id (int): Идентификатор нового пользователя.
        name (str): Имя нового пользователя. По умолчанию пустая строка.
    """ 
    async with async_session() as session:
        user = await get_user(user_id)
        if not user:
            new_user = User(id=user_id, name=name, balance=0.0, is_superuser=False)
            session.add(new_user)
            await session.commit()
        else:
            raise Error409