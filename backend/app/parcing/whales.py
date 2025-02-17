import requests
import json
import asyncio
import aiohttp
import logging
# from utils.config import settings
import aiofiles
from utils.config import settings
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhaleTracker():
    def __init__(self):
        self.helius_api_key = settings.HELIUS_API_KEY
        self.helius_url = settings.HELIUS_URL
        self.min_balance_usd = settings.MIN_WHALE_BALANCE_USD  # e.g., 5000

    async def get_token_holders(self, token_mint_address):
        url = f"{self.helius_url}?api-key={self.helius_api_key}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.helius_api_key}"  # Добавляем заголовок авторизации
        }

        all_owners = set()
        page = 1
        batch_size = 1000  # Maximum allowed by API
        
        while len(all_owners) < 10000:
            params = {
                "jsonrpc": "2.0",
                "method": "getTokenAccounts",
                "id": "helius-test",
                "params": {
                    "mint": token_mint_address,
                    "limit": batch_size,
                    "page": page,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("result") and data["result"]["token_accounts"]:
                            new_owners = {account["owner"] for account in data["result"]["token_accounts"]}
                            all_owners.update(new_owners)
                            logger.info(f"Page {page}: Found {len(new_owners)} token holders. Total: {len(all_owners)}")
                            page += 1
                            if len(new_owners) < batch_size:  # No more holders to fetch
                                break
                        else:
                            logger.warning(f"No token accounts found on page {page}")
                            break
                    else:
                        logger.error(f"Error: Failed to fetch data with status code {response.status}")
                        break
                    
                    await asyncio.sleep(0.1)  # Rate limiting
        
        return all_owners if all_owners else None

    async def get_wallet_balance(self, wallet_address):
        url = f"{self.helius_url}?api-key={self.helius_api_key}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.helius_api_key}"  # Добавляем заголовок авторизации
        }
        
        params = {
            "jsonrpc": "2.0",
            "id": "helius-test",
            "method": "getBalance",
            "params": [wallet_address]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "result" in data:
                        balance_in_sol = data["result"]["value"] / 1e9
                        sol_price_usd = 60  # Example fixed price
                        balance_usd = balance_in_sol * sol_price_usd
                        return balance_usd
                logger.warning(f"Failed to get balance for wallet {wallet_address[:8]}...")
                return 0

    async def process_holders_in_batches(self, holders, api_key, batch_size=50):
        wealthy_holders = []
        holders_list = list(holders)
        total_batches = (len(holders_list) + batch_size - 1) // batch_size
        
        logger.info(f"Starting to process {len(holders_list)} holders in {total_batches} batches")
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(holders_list), batch_size):
                batch = holders_list[i:i + batch_size]
                current_batch = i//batch_size + 1
                logger.info(f"Processing batch {current_batch}/{total_batches}")
                logger.info(f"Batch {current_batch} size: {len(batch)} wallets")
                
                tasks = []
                for holder in batch:
                    task = self.get_wallet_balance(holder, api_key)
                    tasks.append(task)
                    
                balances = await asyncio.gather(*tasks)
                
                batch_wealthy_count = 0
                batch_total_balance = 0
                batch_results = []
                
                for holder, balance in zip(batch, balances):
                    batch_total_balance += balance
                    if balance >= 5000:
                        wealthy_holders.append(holder)
                        batch_wealthy_count += 1
                        batch_results.append(f"{holder[:8]}... (${balance:.2f})")
                
                logger.info(f"Batch {current_batch} stats:")
                logger.info(f"- Total balance: ${batch_total_balance:.2f}")
                logger.info(f"- Average balance: ${batch_total_balance/len(batch):.2f}")
                logger.info(f"- Wealthy holders found: {batch_wealthy_count}")
                if batch_results:
                    logger.info(f"- Wealthy holders: {batch_results}")
                
                await asyncio.sleep(0.1)  # Rate limiting
        
        logger.info(f"Batch processing complete:")
        logger.info(f"- Total holders processed: {len(holders_list)}")
        logger.info(f"- Total wealthy holders found: {len(wealthy_holders)}")
        
        return wealthy_holders
    
    async def analyze_token(self, token_mint_address):
        """Main method to analyze a single token"""
        logger.info(f"Starting whale analysis for token {token_mint_address}")
        holders = await self.get_token_holders(token_mint_address)
        
        if holders:
            wealthy_holders = await self.process_holders_in_batches(holders, self.helius_api_key)
            
            # Prepare data to save
            from datetime import datetime
            data = {
                "timestamp": datetime.now().isoformat(),
                "token_mint": token_mint_address,
                "total_holders": len(holders),
                "wealthy_holders": wealthy_holders,
                "wealthy_holders_count": len(wealthy_holders)
            }
            
            # Generate filename with current datetime
            filename = f"whales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = f"{settings.WHALE_DATA_PATH}/{filename}"
            
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(json.dumps(data, indent=4))
            logger.info(f"Whale data saved to {filepath}")
            return wealthy_holders
        
        logger.error("No holders found to analyze")
        return None

