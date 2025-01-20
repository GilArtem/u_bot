import segno
from io import BytesIO
from aiogram.types import BufferedInputFile

def generate_qr_code(user_id: int):
    deep_link = f'https://t.me/username_u_bot?start=scan_qr_code_user_{user_id}'
    qr = segno.make(deep_link, micro=False)
    
    buffer = BytesIO()
    qr.save(buffer, kind='png', scale=10, dark='black', light='white')
    buffer.seek(0)
    
    return BufferedInputFile(buffer.getvalue(), filename="qr_code.png")