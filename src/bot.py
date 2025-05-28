import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import common, free_sale, our_product


async def main():
    """Основная функция запуска бота"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    # Проверка токена
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Создание бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключение роутеров
    dp.include_router(common.router)
    dp.include_router(free_sale.router)
    dp.include_router(our_product.router)
    
    # Запуск бота
    logging.info("Бот запускается...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
