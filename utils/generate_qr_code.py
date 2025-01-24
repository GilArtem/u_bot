import segno
import os
from dotenv import load_dotenv
from io import BytesIO
from aiogram.types import BufferedInputFile

load_dotenv()

def generate_qr_code(user_id: int):
    deep_link = f'https://t.me/{os.getenv("BOT_USERNAME")}?start=scan_qr_code_user_{user_id}'
    qr = segno.make(deep_link, micro=False)
    
    buffer = BytesIO()
    qr.save(buffer, kind='png', scale=10, dark='black', light='white')
    buffer.seek(0)
    
    return BufferedInputFile(buffer.getvalue(), filename="qr_code.png")