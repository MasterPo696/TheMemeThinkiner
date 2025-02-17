import asyncio
import aiohttp
import logging
from utils.config import settings
import os
import json
from datetime import datetime

# Configure logging to display INFO-level messages
logging.basicConfig(level=logging.INFO)

class DataCollector:
    def __init__(self, endpoints):
        self.base_url = "https://api.dexscreener.com/"  # Можно также использовать settings.DEX_URL
        self.endpoints = endpoints

    async def fetch_data(self, session, endpoint):
        url = f"{self.base_url}{endpoint}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Проверяем, является ли data словарём
                    if isinstance(data, dict):
                        return data
                    # Если data — список, обрабатываем его
                    elif isinstance(data, list):
                        return {'data': data}
                    else:
                        logging.error(f"Unexpected data type received from {url}: {type(data)}")
                        return None
                else:
                    logging.error(f"Failed to fetch data from {url}. Status: {response.status}")
                    return None
        except Exception as e:
            logging.error(f"Error fetching data from {url}: {e}")
            return None

    async def collect_data(self):
        async with aiohttp.ClientSession() as session:
            while True:
                collected_data = []
                for endpoint in self.endpoints:
                    try:
                        data = await self.fetch_data(session, endpoint)
                        if data and isinstance(data, dict):
                            logging.info(f"Successfully fetched data from {endpoint}")
                            collected_data.extend(data.get('data', []))
                    except Exception as e:
                        logging.error(f"Error collecting data from {endpoint}: {e}")
                
                if collected_data:
                    os.makedirs(settings.RAW_DATA_FILEPATH, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{settings.RAW_DATA_FILEPATH}/data_{timestamp}.json"
                    with open(filename, "w") as f:
                        json.dump(collected_data, f, indent=4)
                    logging.info(f"Data successfully saved to {filename}")
                
                # Wait 60 seconds before next collection
                await asyncio.sleep(60)
