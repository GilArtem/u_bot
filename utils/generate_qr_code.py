import segno
from dotenv import load_dotenv
from io import BytesIO
from aiogram.types import BufferedInputFile
from aiogram.utils.deep_linking import create_start_link 


async def generate_qr_code(bot, user_id: int) -> BufferedInputFile:
    """ 
    Генерация QR-кода с глубокой ссылкой для пользователя.
    Используется для процесса списания средств.
    
    Args:
        bot: Экземпляр бота, используемый для создания глубокой ссылки.
        user_id (int): Идентификатор пользователя, для которого создается QR-код.
    """
    deep_link = await create_start_link(bot, payload=str(user_id), encode=True)
    qr = segno.make(deep_link, micro=False)
    
    buffer = BytesIO()
    qr.save(buffer, kind='png', scale=10, dark='black', light='white')
    buffer.seek(0)
    
    return BufferedInputFile(buffer.getvalue(), filename='qr_code.png')


async def generate_qr_code_for_balance_up(bot, user_id: int) -> BufferedInputFile:
    """ 
    Генерация QR-кода с глубокой ссылкой для пополнения баланса пользователя.
    Используется для процесса поплнения баланса.
    
    Args:
        bot: Экземпляр бота, используемый для создания глубокой ссылки.
        user_id (int): Идентификатор пользователя, для которого создается QR-код.
    """
    deep_link = await create_start_link(bot, payload=f"{user_id}:balance_up", encode=True)
    qr = segno.make(deep_link, micro=False)
    
    buffer = BytesIO()
    qr.save(buffer, kind='png', scale=10, dark='black', light='white')
    buffer.seek(0)
    
    return BufferedInputFile(buffer.getvalue(), filename='qr_code.png')