import segno
import os
from dotenv import load_dotenv
from io import BytesIO
from aiogram.types import BufferedInputFile
from .make_short_jwt import generate_short_jwt

load_dotenv()

BOT_USERNAME = os.getenv("BOT_USERNAME")


async def generate_qr_code(user_id: int):
    short_token = await generate_short_jwt(user_id)
    deep_link = f'https://t.me/{BOT_USERNAME}?start=scan_qr_code_user_{short_token}'
    qr = segno.make(deep_link, micro=False)
    
    buffer = BytesIO()
    qr.save(buffer, kind='png', scale=10, dark='black', light='white')
    buffer.seek(0)
    
    return BufferedInputFile(buffer.getvalue(), filename="qr_code.png")