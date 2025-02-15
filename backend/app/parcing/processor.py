import json
import logging
import os
import aiohttp
import aiofiles
from datetime import datetime
from glob import glob

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class TokenManager:
    def __init__(self, data_file="data.json", base_url="https://api.dexscreener.com/latest/dex/tokens"):
        self.data_file = data_file
        self.base_url = base_url
        logging.info(f"TokenManager initialized with data_file={data_file}, base_url={base_url}")

    async def save_data(self, data):
        """Saves token list to JSON file with indentation."""
        logging.info(f"Starting to save data to {self.data_file}")
        async with aiofiles.open(self.data_file, "w") as f:
            await f.write(json.dumps(data, indent=4))
        logging.info(f"Data successfully saved to {self.data_file}")

    async def load_data(self):
        """Loads token data from file. Returns empty list if file not found."""
        logging.info(f"Attempting to load data from {self.data_file}")
        try:
            async with aiofiles.open(self.data_file, "r") as f:
                content = await f.read()
                tokens = json.loads(content)
                logging.info(f"Successfully loaded {len(tokens) if isinstance(tokens, list) else 0} tokens")
                return tokens if isinstance(tokens, list) else []
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Failed to load data: {str(e)}")
            return []

    async def get_token_data(self, token_address):
        """Gets token data from DexScreener API."""
        url = f"{self.base_url}/{token_address}"
        logging.info(f"Fetching token data for address {token_address}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    token_data = data.get("pairs", [])[0] if data.get("pairs") else {}
                    if token_data:
                        logging.info(f"Successfully retrieved data for token {token_address}")
                    else:
                        logging.warning(f"No data found for token {token_address}")
                    return token_data if token_data else {"error": "No data found"}
        except Exception as e:
            logging.error(f"Error fetching token data: {str(e)}")
            return {"error": str(e)}

    async def process_latest_raw_data(self):
        """Process raw data files and save enriched data with full token metrics"""
        logging.info("Starting to process latest raw data")
        
        raw_files = glob('backend/data/raw/data_*.json')
        if not raw_files:
            logging.error("No raw data files found")
            return

        latest_file = max(raw_files)
        logging.info(f"Processing latest file: {latest_file}")
        
        try:
            async with aiofiles.open(latest_file, 'r') as f:
                raw_data = json.loads(await f.read())
                logging.info(f"Loaded {len(raw_data)} tokens from raw data")

            enriched_data = []
            async with aiohttp.ClientSession() as session:
                for i, token in enumerate(raw_data):
                    token_address = token.get("contract", {}).get("address")
                    if token_address:
                        logging.info(f"Processing token {i+1}/{len(raw_data)}: {token_address}")
                        token_details = await self.get_token_data(token_address)
                        if not token_details.get("error"):
                            enriched_data.append({**token, **token_details})
                            logging.info(f"Successfully enriched data for token {token_address}")
                        else:
                            enriched_data.append(token)
                            logging.warning(f"Using original data for token {token_address} due to error")

            os.makedirs('backend/data/clean', exist_ok=True)
            timestamp = latest_file.split('data_')[1].split('.json')[0]
            clean_filename = f'backend/data/clean/data_{timestamp}.json'
            
            logging.info(f"Saving enriched data to {clean_filename}")
            async with aiofiles.open(clean_filename, 'w') as f:
                await f.write(json.dumps(enriched_data, indent=4))

            logging.info(f"Successfully saved enriched data for {len(enriched_data)} tokens to {clean_filename}")

        except Exception as e:
            logging.error(f"Error processing raw data: {str(e)}")

if __name__ == '__main__':
    import asyncio
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting TokenManager main execution")
    manager = TokenManager()
    asyncio.run(manager.process_latest_raw_data())
    logging.info("TokenManager execution completed")


# import json
# import logging
# import requests
# import os
# from datetime import datetime
# from glob import glob

# class TokenManager:
#     def __init__(self, data_file="data.json", base_url="https://api.dexscreener.com/latest/dex/tokens"):
#         self.data_file = data_file
#         self.base_url = base_url

#     def save_data(self, data):
#         """Saves token list to JSON file with indentation."""
#         with open(self.data_file, "w") as f:
#             json.dump(data, f, indent=4)
#         logging.info(f"Data saved to {self.data_file}")

#     def load_data(self):
#         """Loads token data from file. Returns empty list if file not found."""
#         try:
#             with open(self.data_file, "r") as f:
#                 tokens = json.load(f)
#                 if not isinstance(tokens, list):
#                     return []
#                 return tokens
#         except (FileNotFoundError, json.JSONDecodeError):
#             return []

#     def process_data(self, tokens, as_json=True):
#         """
#         Processes token list, returning network name, contract data, liquidity and price changes.

#         Args:
#             tokens (list): List of token data dictionaries
#             as_json (bool): If True, returns JSON string with indentation, else returns list

#         Returns formatted data with:
#             - Network info
#             - Contract details  
#             - Price changes over time
#             - Current prices
#             - Volume data
#             - Liquidity info
#             - Transaction counts
#             - Market metrics
#         """
#         processed = []
#         for token in tokens:
#             processed_token = {
#                 "network": token.get("chainId") or token.get("network"),
#                 "contract": {
#                     "address": token.get("tokenAddress") or (token.get("contract") and token.get("contract").get("address")),
#                     "link": token.get("url") or (token.get("contract") and token.get("contract").get("link"))
#                 },
#                 "price_changes": {
#                     "m5": token.get("priceChange", {}).get("m5", 0.0),
#                     "h1": token.get("priceChange", {}).get("h1", 0.0), 
#                     "h6": token.get("priceChange", {}).get("h6", 0.0),
#                     "h24": token.get("priceChange", {}).get("h24", 0.0)
#                 },
#                 "current_price": {
#                     "native": token.get("priceNative", 0.0),
#                     "usd": token.get("priceUsd", 0.0)
#                 },
#                 "volume": {
#                     "m5": token.get("volume", {}).get("m5", 0.0),
#                     "h1": token.get("volume", {}).get("h1", 0.0),
#                     "h6": token.get("volume", {}).get("h6", 0.0), 
#                     "h24": token.get("volume", {}).get("h24", 0.0)
#                 },
#                 "liquidity": token.get("liquidity", {
#                     "usd": 0.0,
#                     "base": 0.0,
#                     "quote": 0.0
#                 }),
#                 "transactions": {
#                     "m5": token.get("txns", {}).get("m5", {"buys": 0, "sells": 0}),
#                     "h1": token.get("txns", {}).get("h1", {"buys": 0, "sells": 0}),
#                     "h6": token.get("txns", {}).get("h6", {"buys": 0, "sells": 0}),
#                     "h24": token.get("txns", {}).get("h24", {"buys": 0, "sells": 0})
#                 },
#                 "market_cap": token.get("marketCap", 0.0),
#                 "fdv": token.get("fdv", 0.0)
#             }
#             processed.append(processed_token)
            
#         return json.dumps(processed, indent=4) if as_json else processed

#     def add_new_token(self, network, token_address, token_url=None):
#         """
#         Adds new token to data file. Generates URL if not provided.

#         Args:
#             network (str): Network or token name
#             token_address (str): Token address
#             token_url (str, optional): Token URL

#         Returns:
#             dict: Added token data
#         """
#         if token_url is None:
#             token_url = f"https://dexscreener.com/{network.lower()}/{token_address.lower()}"

#         new_token = {
#             "network": network,
#             "contract": {
#                 "address": token_address,
#                 "link": token_url
#             }
#         }

#         tokens = self.load_data()
#         tokens.append(new_token)
#         self.save_data(tokens)
#         logging.info(f"New token '{network}' added to {self.data_file}")
#         return new_token

#     def get_token_data(self, token_address, chain_id="solana"):
#         """
#         Gets token data from DexScreener API.

#         Args:
#             token_address (str): Token address
#             chain_id (str): Network ID (default 'solana')

#         Returns:
#             dict: Token data or error message
#         """
#         url = f"{self.base_url}/{token_address}"
#         try:
#             response = requests.get(url)
#             data = response.json().get("pairs", [])[0] if response.json().get("pairs") else {}

#             if not data:
#                 return {"error": "No data found"}

#             return {
#                 "token_address": token_address,
#                 "price_changes": {
#                     "m5": data.get("priceChange", {}).get("m5", 0.0),
#                     "h1": data.get("priceChange", {}).get("h1", 0.0),
#                     "h6": data.get("priceChange", {}).get("h6", 0.0),
#                     "h24": data.get("priceChange", {}).get("h24", 0.0)
#                 },
#                 "current_price": {
#                     "native": data.get("priceNative", 0.0),
#                     "usd": data.get("priceUsd", 0.0)
#                 },
#                 "volume": {
#                     "m5": data.get("volume", {}).get("m5", 0.0),
#                     "h1": data.get("volume", {}).get("h1", 0.0),
#                     "h6": data.get("volume", {}).get("h6", 0.0),
#                     "h24": data.get("volume", {}).get("h24", 0.0)
#                 },
#                 "liquidity": data.get("liquidity", {"usd": 0.0, "base": 0.0, "quote": 0.0}),
#                 "transactions": {
#                     "m5": data.get("txns", {}).get("m5", {"buys": 0, "sells": 0}),
#                     "h1": data.get("txns", {}).get("h1", {"buys": 0, "sells": 0}),
#                     "h6": data.get("txns", {}).get("h6", {"buys": 0, "sells": 0}),
#                     "h24": data.get("txns", {}).get("h24", {"buys": 0, "sells": 0})
#                 },
#                 "market_cap": data.get("marketCap", 0.0),
#                 "fdv": data.get("fdv", 0.0)
#             }
#         except Exception as e:
#             return {"error": str(e)}

#     def process_latest_raw_data(self):
#         """Process raw data files and save enriched data with full token metrics"""
#         raw_files = glob('data/raw/data_*.json')
#         if not raw_files:
#             logging.error("No raw data files found")
#             return
        
#         latest_file = max(raw_files)
        
#         try:
#             with open(latest_file, 'r') as f:
#                 raw_data = json.load(f)
            
#             enriched_data = []
#             for token in raw_data:
#                 token_address = token.get("contract", {}).get("address")
#                 network = token.get("network", "solana")
                
#                 if token_address:
#                     token_details = self.get_token_data(token_address, network)
#                     if not token_details.get("error"):
#                         enriched_data.append({**token, **token_details})
#                     else:
#                         enriched_data.append(token)
            
#             os.makedirs('data/clean', exist_ok=True)
            
#             timestamp = latest_file.split('data_')[1].split('.json')[0]
#             clean_filename = f'data/clean/data_{timestamp}.json'
            
#             with open(clean_filename, 'w') as f:
#                 json.dump(enriched_data, f, indent=4)
                
#             logging.info(f"Enriched data saved to {clean_filename}")
            
#         except Exception as e:
#             logging.error(f"Error processing raw data: {str(e)}")

# if __name__ == '__main__':
#     logging.basicConfig(level=logging.INFO)
#     manager = TokenManager()
    
#     # Process latest raw data file with full token metrics
#     manager.process_latest_raw_data()
