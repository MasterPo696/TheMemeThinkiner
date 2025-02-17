import json
import os
import glob
import asyncio
import websockets
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhaleSubscription:
    def __init__(self):
        self.whales_dir = "/Users/masterpo/Desktop/TheThinker/backend/data/whales"
        self.wealthy_holders = self._get_latest_whale_data()
        self.ws_url = "wss://mainnet.helius-rpc.com/?api-key=29291e23-0902-4433-a6a7-2f3e32495ee7"

    def _get_latest_whale_data(self):
        # Get list of all json files in whales directory
        json_files = glob.glob(os.path.join(self.whales_dir, "*.json"))
        
        if not json_files:
            logger.error("No whale data files found")
            asyncio.sleep(5)
            return []

        # Find the latest file based on timestamp in filename
        latest_file = max(json_files, key=lambda x: os.path.getctime(x))
        
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded whale data from {latest_file}")
                return data.get('wealthy_holders', [])
        except Exception as e:
            logger.error(f"Error loading whale data: {e}")
            return []

    async def subscribe_to_transactions(self):
        while True:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    # Subscribe to all wealthy holder addresses
                    subscribe_message = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "accountSubscribe",
                        "params": [
                            self.wealthy_holders,
                            {"encoding": "jsonParsed", "commitment": "confirmed"}
                        ]
                    }
                    
                    await websocket.send(json.dumps(subscribe_message))
                    logger.info(f"Subscribed to {len(self.wealthy_holders)} whale addresses")

                    while True:
                        try:
                            response = await websocket.recv()
                            data = json.loads(response)
                            
                            if "params" in data:
                                transaction = data["params"]
                                logger.info(f"New transaction detected: {transaction}")
                                # Here you can add logic to process the transaction
                                # For example, send alerts if transaction amount exceeds threshold
                                
                        except websockets.ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            break
                            
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting

async def main():
    subscription = WhaleSubscription()
    await subscription.subscribe_to_transactions()

if __name__ == "__main__":
    asyncio.run(main())
