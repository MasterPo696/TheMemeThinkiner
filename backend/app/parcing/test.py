import aiohttp
import asyncio

async def get_token_holders(token_mint_address):
    url = "https://mainnet.helius-rpc.com/?api-key=29291e23-0902-4433-a6a7-2f3e32495ee7"
    headers = {
        "Content-Type": "application/json"
    }

    params = {
        "jsonrpc": "2.0",
        "method": "getTokenAccounts",
        "id": "helius-test",
        "params": {
            "mint": token_mint_address,
            "limit": 1000,
            "page": 1
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("result") and data["result"]["token_accounts"]:
                    return [account["owner"] for account in data["result"]["token_accounts"]]
                else:
                    return []
            else:
                print(f"Error: {response.status}")
                return []

async def main():
    token_mint_address = "CePv8Wsf46tjzyVvrwBArptYhifvRKwQ2qD7hYf4pump"
    holders = await get_token_holders(token_mint_address)
    print(holders)

if __name__ == "__main__":
    asyncio.run(main()) 