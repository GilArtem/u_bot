from aiogram import Router, types, Bot
import asyncio
from aiogram.types import ReplyKeyboardRemove, Message
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter, TelegramUnauthorizedError, TelegramNetworkError, TelegramAPIError
from functools import wraps
from instance import logger, bot
from aiohttp import ClientConnectorError
from errors.errors import *

router = Router()


@router.error()
async def global_error_handler(update: types.Update, exception: Exception):
    if isinstance(exception, TelegramBadRequest):
        logger.error(f"Некорректный запрос: {exception}. Пользователь: {update.message.from_user.id}")
        return True
    elif isinstance(exception, TelegramRetryAfter):
        logger.error(f"Request limit exceeded. Retry after {exception.retry_after} seconds.")
        await asyncio.sleep(exception.retry_after)
        return True
    elif isinstance(exception, TelegramUnauthorizedError):
        logger.error(f"Authorization error: {exception}")
        return True
    elif isinstance(exception, TelegramNetworkError):
        logger.error(f"Network error: {exception}")
        await asyncio.sleep(5)
        await safe_send_message(bot, update.message.chat.id, text="Повторная попытка...")
        return True
    elif isinstance(exception, TelegramAPIError):
        # Обработка ошибок API Telegram
        print(f"Telegram API error: {exception}")
    else:
        logger.exception(f"Неизвестная ошибка: {exception}")
        return True

    # Отправка сообщения администратору или логирование ошибки
    admin_ids = [1111433822]  # Замените на ваши ID администраторов
    for admin_id in admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=f"Произошла ошибка: {exception}")
        except Exception as e:
            print(f"Failed to send error message to admin: {e}")
            

def db_error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Error404 as e:
            logger.error(f"Ошибка 404: {str(e)}")
            return None
        except DatabaseConnectionError as e:
            logger.error(f"Ошибка соединения с базой данных: {str(e)}")
            return None
        except Error409 as e:
            logger.error(f"Ошибка 409: {str(e)}")
            return None
        except Exception as e:
            logger.exception(f"Неизвестная ошибка в {func.__name__}: {str(e)}")
            raise  # Перевыбрасываем исключение для отладки
    return wrapper


async def safe_send_message(bott: Bot, recipient, text: str, reply_markup=ReplyKeyboardRemove(), retry_attempts=3, delay=5) -> Message:
    """Отправка сообщения с обработкой ClientConnectorError, поддержкой reply_markup и выбором метода отправки."""

    for attempt in range(retry_attempts):
        try:
            if isinstance(recipient, types.Message):
                msg = await recipient.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            elif isinstance(recipient, types.CallbackQuery):
                msg = await recipient.message.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            elif isinstance(recipient, int):
                msg = await bott.send_message(chat_id=recipient, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                raise TypeError(f"Неподдерживаемый тип recipient: {type(recipient)}")

            return msg

        except ClientConnectorError as e:
            logger.error(f"Ошибка подключения: {e}. Попытка {attempt + 1} из {retry_attempts}.")
            if attempt < retry_attempts - 1:
                await asyncio.sleep(delay)
            else:
                logger.error(f"Не удалось отправить сообщение после {retry_attempts} попыток.")
                return None
        except Exception as e:
            #logger.error(str(e))
            logger.exception(f"Unexpected error: {e}")
            return None
