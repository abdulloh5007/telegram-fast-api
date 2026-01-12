import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from bot import routers, storage


async def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not set")
        return
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    for router in routers:
        dp.include_router(router)
    
    print("Bot started")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        for uid in list(storage.clients.keys()):
            client = storage.get_client(uid)
            if client:
                try:
                    await client.disconnect()
                except:
                    pass
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
