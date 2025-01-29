import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from jwt import ExpiredSignatureError, InvalidTokenError
from database.req_short_token import save_short_token, validate_short_token
from sqlalchemy import select

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY") 
ALGORITHM = os.getenv("ALGORITHM")
EXP_DELTA_SECONDS = os.getenv("EXP_DELTA_SECONDS") 

async def generate_short_jwt(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=int(EXP_DELTA_SECONDS))
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    short_token = token[90:]  
    expires_at = payload["exp"]
    short_token = await save_short_token(user_id, short_token, expires_at)
        
    return short_token


async def validate_short_jwt(short_token: str) -> int:
    if short_token.startswith("scan_qr_code_user_"):
        short_token = short_token[len("scan_qr_code_user_"):]
        token_data = await validate_short_token(short_token)
        
    if not token_data:
        raise InvalidTokenError("Токен не найден в базе данных.")

    user_id, expires_at = token_data
    if datetime.now(timezone.utc) > expires_at:
        raise ExpiredSignatureError("Срок действия токена истек.")
        
    return user_id