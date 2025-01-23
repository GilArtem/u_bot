import asyncio

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from confige import BotConfig
from database.req_user import *
from handlers import errors, user, admin
from instance import bot
from database.models import async_main

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.models import TransactionRequest, async_session
from datetime import datetime, timedelta

# def register_routers(dp: Dispatcher) -> None:
#     dp.include_routers(errors.router, user.router, admin.router)


# async def main() -> None:
#     await async_main()

#     config = BotConfig(
#         admin_ids=[1111433822],
#         welcome_message="Добро пожаловать в U-bot!"
#     )
#     dp = Dispatcher(storage=MemoryStorage())
#     dp["config"] = config

#     register_routers(dp)

#     try:
#         await dp.start_polling(bot, skip_updates=True)
#     except Exception as _ex:
#         print(f'Exception: {_ex}')


# async def check_expired_transactions():
#     async with async_session() as session:
#         requests = await session.execute(
#             select(TransactionRequest).where(
#                 TransactionRequest.status == 'in_process',
#                 TransactionRequest.created_at < datetime.utcnow() - timedelta(hours=1)
#             )
#         )
#         for request in requests.scalars():
#             request.status = 'expired'
#         await session.commit()

# scheduler = AsyncIOScheduler()
# scheduler.add_job(check_expired_transactions, 'interval', hours=1)
# scheduler.start()


# if __name__ == '__main__':
#     asyncio.run(main())





def register_routers(dp: Dispatcher) -> None:
    dp.include_routers(errors.router, user.router, admin.router)

async def check_expired_transactions():
    async with async_session() as session:
        requests = await session.execute(
            select(TransactionRequest).where(
                TransactionRequest.status == 'in_process',
                TransactionRequest.created_at < datetime.utcnow() - timedelta(hours=1)
            )
        )
        for request in requests.scalars():
            request.status = 'expired'
        await session.commit()

async def main() -> None:
    await async_main()
    config = BotConfig(
        admin_ids=[1111433822],
        welcome_message="Добро пожаловать в U-bot!"
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp["config"] = config
    register_routers(dp)
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_expired_transactions, 'interval', hours=1)
    
    try:
        await dp.start_polling(bot, skip_updates=True)
        scheduler.start()
    except Exception as _ex:
        print(f'Exception: {_ex}')

if __name__ == '__main__':
    asyncio.run(main())