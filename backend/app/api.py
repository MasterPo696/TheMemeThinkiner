from aiohttp import web
import aiohttp


# Функция для получения данных о китах из GMGN API
async def fetch_whale_data():
    # Пример URL – уточните его согласно документации
    url = "https://api.gmgn.ai/solana/trading/whales"
    try:
        async with aiohttp.ClientSession() as session:
            # Если требуется авторизация или дополнительные заголовки, добавьте параметр headers
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"Ошибка запроса к GMGN API: {response.status}")
                    return None
    except Exception as e:
        print("Ошибка при запросе данных от GMGN API:", e)
        return None
    

    
    

async def get_data(request):
    # Логика получения данных (из БД или кэша)
    data = {"status": "ok", "data": "Информация о китах"}
    return web.json_response(data)

app = web.Application()
app.router.add_get('/api/data', get_data)

if __name__ == '__main__':
    web.run_app(app, port=8080)
