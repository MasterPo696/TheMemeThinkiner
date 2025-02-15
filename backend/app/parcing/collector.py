import asyncio
import aiohttp
import logging
from backend.app.utils.config import settings
import os
import json
from datetime import datetime
from backend.app.parcing.processor import TokenManager



# Configure logging to display INFO-level messages
logging.basicConfig(level=logging.INFO)

# print(settings.DEX_URL)  # Автоматически загрузит из .env
class DataCollector:
    def __init__(self, endpoints):
        self.base_url = "https://api.dexscreener.com/"  # Можно также использовать settings.DEX_URL
        self.endpoints = endpoints
        self.token_processor = TokenManager()  # Initialize the processor

    async def fetch_data(self, session, endpoint):
        url = f"{self.base_url}{endpoint}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Failed to fetch data from {url}. Status: {response.status}")
                    return None
        except Exception as e:
            logging.error(f"Error fetching data from {url}: {e}")
            return None

    async def data_collector(self):
        async with aiohttp.ClientSession() as session:
            while True:
                collected_data = []
                for endpoint in self.endpoints:
                    try:
                        data = await self.fetch_data(session, endpoint)
                        if data:
                            logging.info(f"Successfully fetched data from {endpoint}")
                            processed = json.loads(self.token_processor.process_data(data))  # Use the processor
                            collected_data.extend(processed)
                    except Exception as e:
                        logging.error(f"Error collecting data from {endpoint}: {e}")
                if collected_data:
                    # Создаём папку 'data', если она ещё не существует
                    os.makedirs("data", exist_ok=True)
                    # Format current timestamp as YYYYMMDD_HHMMSS
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # Construct filename with timestamp in data/raw directory
                    filename = f"data/raw/data_{timestamp}.json"
                    with open(filename, "w") as f:
                        json.dump(collected_data, f, indent=4)
                    logging.info(f"Data successfully saved to {filename}")
                # Ждем 20 секунд перед следующим сохранением
                await asyncio.sleep(20)

# Определяем эндпоинты для сбора данных
endpoints = ["/token-profiles/latest/v1", "/token-boosts/latest/v1"]

# Создаем экземпляр сборщика данных
collector = DataCollector(endpoints=endpoints)

# Запускаем сбор данных
asyncio.run(collector.data_collector())

