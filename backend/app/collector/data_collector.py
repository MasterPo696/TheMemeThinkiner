import asyncio
import aiohttp
import settings


# print(settings.DEX_URL)  # Автоматически загрузит из .env

class DataCollector():
    async def __init__(self, url, key=None):
        self.url = url
        self.__key = key
        
    # Fetching the url and getting data (json)
    async def fetch_data(self, session, url):
        async with session.get(url) as response:
            return await response.json()
        
    async def data_collector(self):
        return
        


