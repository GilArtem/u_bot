from datetime import datetime

from sqlalchemy import select
from database.models import ShortToken
from database.models import async_session
from sqlalchemy.exc import IntegrityError
from handlers.errors import db_error_handler
from errors.errors import *


@db_error_handler
async def save_short_token(user_id: int, short_token: str, expires_at: datetime):
    async with async_session() as session:
        try:
            new_token = ShortToken(
                user_id=user_id,
                short_token=short_token,
                expires_at=expires_at
            )
            session.add(new_token)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise ValueError("Не удалось сохранить токен в базе данных.")
    return short_token
    

@db_error_handler
async def validate_short_token(short_token: str):
    async with async_session() as session:
        
        result = await session.execute(
            select(ShortToken.user_id, ShortToken.expires_at)
            .where(ShortToken.short_token == short_token)
        )
        token_data = result.fetchone()
    return token_data
        
        