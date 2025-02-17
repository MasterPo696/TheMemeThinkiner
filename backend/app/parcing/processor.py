import json
import logging
import os
import aiohttp
import aiofiles
from datetime import datetime
from glob import glob
from parcing.whales import WhaleTracker
from utils.config import settings
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class TokenManager:
    def __init__(self, data_file="data.json", base_url="https://api.dexscreener.com/latest/dex/tokens"):
        self.data_file = data_file
        self.base_url = base_url
        self.raw_data_path = "/Users/masterpo/Desktop/TheThinker/backend/data/raw"
        self.clean_data_path = "/Users/masterpo/Desktop/TheThinker/backend/data/clean"
        self.pumped_data_path = "/Users/masterpo/Desktop/TheThinker/backend/data/pumped"
        self.whale_tracker = WhaleTracker()  # Add WhaleTracker instance
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

    def filter_pumped_tokens(self, enriched_data):
        """Filter tokens with more than 50% price growth in 24h"""
        pumped_tokens = []
        for token in enriched_data:
            try:
                price_change_24h = float(token.get('priceChange', {}).get('h24', 0))
                if price_change_24h > 50:
                    pumped_token_info = {
                        'name': token.get('baseToken', {}).get('name'),
                        'contract': token.get('baseToken', {}).get('address'),
                        'growth_24h': price_change_24h
                    }
                    pumped_tokens.append(pumped_token_info)
                    logging.info(f"Token {token.get('baseToken', {}).get('symbol')} pumped {price_change_24h}% in 24h")
            except (ValueError, TypeError, AttributeError) as e:
                logging.warning(f"Could not process price change for token: {e}")
        return pumped_tokens

    async def process_latest_raw_data(self):
        """Process raw data files and save enriched data with full token metrics"""
        logging.info("Starting to process latest raw data")
        
        raw_files = glob(os.path.join(self.raw_data_path, 'data_*.json'))
        if not raw_files:
            logging.error("No raw data files found")
            return None

        latest_file = max(raw_files)
        logging.info(f"Processing latest file: {latest_file}")
        
        try:
            async with aiofiles.open(latest_file, 'r') as f:
                raw_data = json.loads(await f.read())
                logging.info(f"Loaded {len(raw_data)} tokens from raw data")

            enriched_data = []
            async with aiohttp.ClientSession() as session:
                for i, token in enumerate(raw_data):
                    token_address = token.get("tokenAddress")  # Changed this line
                    if token_address:
                        logging.info(f"Processing token {i+1}/{len(raw_data)}: {token_address}")
                        token_details = await self.get_token_data(token_address)
                        if not token_details.get("error"):
                            enriched_data.append({**token, **token_details})
                            logging.info(f"Successfully enriched data for token {token_address}")
                        else:
                            enriched_data.append(token)
                            logging.warning(f"Using original data for token {token_address} due to error")

            # Save enriched data
            os.makedirs('backend/data/clean', exist_ok=True)
            timestamp = latest_file.split('data_')[1].split('.json')[0]
            clean_filename = f'backend/data/clean/data_{timestamp}.json'
            
            logging.info(f"Saving enriched data to {clean_filename}")
            async with aiofiles.open(clean_filename, 'w') as f:
                await f.write(json.dumps(enriched_data, indent=4))

            # Filter and save pumped tokens
            pumped_tokens = self.filter_pumped_tokens(enriched_data)
            if pumped_tokens:
                os.makedirs('backend/data/pumped', exist_ok=True)
                timestamp = latest_file.split('data_')[1].split('.json')[0]
                pumped_filename = f'backend/data/pumped/data_{timestamp}.json'
                logging.info(f"Saving {len(pumped_tokens)} pumped tokens to {pumped_filename}")
                
                # Save pumped tokens
                async with aiofiles.open(pumped_filename, 'w') as f:
                    await f.write(json.dumps(pumped_tokens, indent=4))

                # Track whales for each pumped token
                whale_results = []
                for token in pumped_tokens:
                    token_address = token.get('contract')
                    if token_address:
                        logging.info(f"Analyzing whales for token: {token_address}")
                        wealthy_holders = await self.whale_tracker.analyze_token(token_address)
                        if wealthy_holders:
                            whale_results.append({
                                'token': token_address,
                                'wealthy_holders': wealthy_holders
                            })

                return pumped_tokens  # Return pumped tokens for further processing

            logging.info(f"Successfully processed data for {len(enriched_data)} tokens")
            return None

        except Exception as e:
            logging.error(f"Error processing raw data: {str(e)}")
            return None