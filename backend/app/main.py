import asyncio
from parcing.whales import WhaleTracker


async def main():
    detector = WhaleTracker()

    # 1. Асинхронная загрузка токенов из Data/clean.json
    tokens = await detector.load_tokens()

    # 2. Фильтрация токенов с высоким ростом (например, рост >= 50%)
    high_growth_tokens = detector.filter_high_growth_tokens(tokens, growth_threshold=50)

    all_whales = []
    # 3. Для каждого токена получаем транзакции и анализируем сделки
    for token in high_growth_tokens:
        token_contract = token.get("contract")
        if token_contract:
            whales = await detector.process_transactions(token_contract)
            # Фильтруем кандидатов по критерию: например, прибыльные сделки (PnL > 0)
            filtered_whales = [w for w in whales if w["pnl"] > 0]
            all_whales.extend(filtered_whales)

    # 4. Асинхронное сохранение списка китов в Data/whales.json
    await detector.save_whales(all_whales)

    # 5. Запуск подписки для мониторинга активности китов (раскомментируйте, если нужно)
    # await detector.subscribe_whales(all_whales)

if __name__ == "__main__":
    asyncio.run(main())
