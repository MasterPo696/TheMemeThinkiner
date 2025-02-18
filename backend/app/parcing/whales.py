import json
import asyncio
import aiohttp
import logging
import aiofiles
from utils.config import settings
# Set up logging
from utils.slogger import SmartLogger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class WhaleTracker():
    def __init__(self):
        self.helius_api_key = settings.HELIUS_API_KEY
        self.helius_url = settings.HELIUS_URL
        self.min_balance_usd = settings.MIN_WHALE_BALANCE_USD  # e.g., 5000
        self.logger = SmartLogger("WhaleTracker", batch_size=10, flush_interval=30)

    async def get_token_holders(self, token_mint_address):
        url = f"{self.helius_url}{self.helius_api_key}"

        headers = {
            "Content-Type": "application/json"
        }

        all_owners = set()
        page = 1
        batch_size = 1000

            
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
        url = f"{self.helius_url}{self.helius_api_key}"
        headers = {
            "Content-Type": "application/json"
        }

        params = {
            "jsonrpc": "2.0",
            "id": "helius-test",
            "method": "getBalance",
            "params": [wallet_address]
        }

        # Implement exponential backoff
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "result" in data:
                                balance_in_sol = data["result"]["value"] / 1e9
                                sol_price_usd = 171.5  # Example fixed price
                                balance_usd = balance_in_sol * sol_price_usd
                                # Increased sleep time to avoid rate limiting
                                await asyncio.sleep(0.5)  
                                return balance_usd
                        elif response.status == 429:
                            delay = base_delay * (2 ** attempt)  # Exponential backoff
                            await asyncio.sleep(delay)
                            continue
                        else:
                            await asyncio.sleep(0.5)
                            return 0
            except Exception as e:
                self.logger.error(f"Error getting balance for {wallet_address}: {e}")
                await asyncio.sleep(0.5)
        return 0


        
    async def process_holders_in_batches(self, holders, api_key, batch_size=25):  # Reduced batch size
        wealthy_holders = []
        holders_list = list(holders)
        total_batches = (len(holders_list) + batch_size - 1) // batch_size
        
        try:
            await self.logger.info(f"Starting to process {len(holders_list)} holders in {total_batches} batches")
        except Exception as e:
            logger.error(f"Error logging batch start: {e}")
        
        batch_stats = {
            "processed": 0,
            "wealthy": 0,
            "total_balance": 0,
            "warnings": 0
        }

        async with aiohttp.ClientSession() as session:
            for i in range(0, len(holders_list), batch_size):
                batch = holders_list[i:i + batch_size]
                current_batch = i//batch_size + 1
                
                # Process batch with delay between each request
                balances = []
                for holder in batch:
                    balance = await self.get_wallet_balance(holder)
                    balances.append(balance)
                    await asyncio.sleep(0.5)  # Add delay between individual requests
                
                batch_wealthy = []
                for holder, balance in zip(batch, balances):
                    batch_stats["total_balance"] += balance
                    batch_stats["processed"] += 1
                    
                    if balance >= self.min_balance_usd:
                        wealthy_holders.append(holder)
                        batch_wealthy.append(f"{holder[:8]}... (${balance:.2f})")
                        batch_stats["wealthy"] += 1
                    elif balance == 0:
                        batch_stats["warnings"] += 1
                
                try:
                    if current_batch % 5 == 0 or current_batch == total_batches:
                        await self.logger.info(
                            f"Batch Progress Summary:\n"
                            f"- Processed: {batch_stats['processed']}/{len(holders_list)}\n"
                            f"- Wealthy found: {batch_stats['wealthy']}\n"
                            f"- Average balance: ${batch_stats['total_balance']/batch_stats['processed']:.2f}\n"
                            f"- Warnings: {batch_stats['warnings']}"
                        )
                    
                    if batch_wealthy:
                        await self.logger.info(f"New wealthy holders in batch {current_batch}: {batch_wealthy}")
                except Exception as e:
                    logger.error(f"Error logging batch progress: {e}")
                
                # Add delay between batches
                await asyncio.sleep(2)  # Increased delay between batches
        
        return wealthy_holders

    async def analyze_token(self, token_mint_address):
        """Main method to analyze a single token"""
        logger.info(f"Starting whale analysis for token {token_mint_address}")
        holders = await self.get_token_holders(token_mint_address)
        #holders = None J8A3ySxv6a8Fy1usD3kjznc2ySQMze3nsRngr7Xvpump
        
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

