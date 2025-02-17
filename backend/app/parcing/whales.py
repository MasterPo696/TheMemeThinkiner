import requests
import json
import asyncio
import aiohttp
import logging
# from utils.config import settings
import aiofiles

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhaleTracker():
    def __init__(self, address, balance=1000):
        self.address = address
        self.balance = balance

    async def get_token_holders(self, token_mint_address, api_key):
        url = "https://mainnet.helius-rpc.com/?api-key=" + api_key
        headers = {
            "Content-Type": "application/json",
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

    async def get_wallet_balance(self, wallet_address, api_key):
        url = "https://mainnet.helius-rpc.com/?api-key=" + api_key
        headers = {
            "Content-Type": "application/json",
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

token_mint_address = "ExZS1zbG7qopJvA87efQDysHrnJxyjzt8FgVyiLijZwM"

HELIUS_API_KEY="29291e23-0902-4433-a6a7-2f3e32495ee7" 
tracker = WhaleTracker(token_mint_address, HELIUS_API_KEY)

async def main():
    token_mint_address = "ExZS1zbG7qopJvA87efQDysHrnJxyjzt8FgVyiLijZwM"
    api_key = "29291e23-0902-4433-a6a7-2f3e32495ee7"  # Replace with your API key
    
    logger.info("Starting token holder analysis...")
    holders = await tracker.get_token_holders(token_mint_address, api_key)
    
    if holders:
        wealthy_holders = await tracker.process_holders_in_batches(holders, api_key)
        logger.info(f"Analysis complete. Found {len(wealthy_holders)} wealthy holders")
        logger.info(f"Summary of wealthy holders: {[h[:8]+'...' for h in wealthy_holders]}")
        
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
        filename = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = "/Users/masterpo/Desktop/TheThinker/backend/data/whales/" + filename
        
        # Save to JSON file using aiofiles
       
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(json.dumps(data, indent=4))
        logger.info(f"Data saved to {filepath}")
    else:
        logger.error("No holders found to analyze")

if __name__ == "__main__":
    asyncio.run(main())
