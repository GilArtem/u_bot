from database.models import User, async_session
from database.req_user import get_user
from errors.errors import *


async def create_user(user_id: int, name: str = ""):  
    async with async_session() as session:
        user = await get_user(user_id)
        if not user:
            new_user = User(id=user_id, name=name, balance=0.0, is_superuser=False)
            session.add(new_user)
            await session.commit()
        else:
            raise Error409