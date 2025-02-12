import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from api import fetch_whale_data
from config import settings

API_TOKEN = settings.BOT_TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Привет! Я бот для отслеживания движений китов.")

# Функция, отправляющая уведомления в Telegram-канал с данными о китах
async def scheduled_notifications():
    while True:
        data = await fetch_whale_data()
        if data:
            # Предполагаем, что API возвращает JSON с ключом "whales", содержащим список операций
            whales = data.get("whales", [])
            if whales:
                for whale in whales:
                    # Предполагаем, что каждый элемент содержит поля "project" и "amount"
                    project = whale.get("project", "неизвестно")
                    amount = whale.get("amount", "N/A")
                    text = f"Кит активен:\nПроект: {project}\nСумма сделки: {amount}"
                    await bot.send_message(chat_id='@your_channel', text=text)
            else:
                await bot.send_message(chat_id='@your_channel', text="Нет новых данных о китах.")
        else:
            await bot.send_message(chat_id='@your_channel', text="Ошибка получения данных от GMGN API.")
        # Пауза между проверками (60 секунд, можно изменить по необходимости)
        await asyncio.sleep(60)

# Главная корутина, запускающая поллинг и фоновую задачу уведомлений
async def main():
    # Запускаем задачу отправки уведомлений в фоне
    asyncio.create_task(scheduled_notifications())
    # Запускаем поллинг бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
