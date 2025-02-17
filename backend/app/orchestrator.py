import asyncio
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from parcing.collector import DataCollector
from parcing.processor import TokenManager
from parcing.whales import WhaleTracker
from parcing.subscription import WhaleSubscription
from utils.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




class DataFileHandler(FileSystemEventHandler):
    def __init__(self, processor, whale_tracker, loop):
        self.processor = processor
        self.whale_tracker = whale_tracker
        self.loop = loop
        
    async def process_new_file(self, file_path):
        # Process raw data to clean data and find pumped tokens
        pumped_tokens = await self.processor.process_latest_raw_data()
        
        # Analyze each pumped token for whales
        if pumped_tokens:
            for token in pumped_tokens:
                wealthy_holders = await self.whale_tracker.analyze_token(token['mint'])
                if wealthy_holders:
                    # Start monitoring these whale addresses
                    await self.whale_subscription.add_addresses(wealthy_holders)


    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.json') and '/raw/' in event.src_path:
            logger.info(f"New raw data detected: {event.src_path}")
            asyncio.run_coroutine_threadsafe(
                self.process_new_file(event.src_path),
                self.loop
            )

class Orchestrator:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.collector = DataCollector(settings.ENDPOINTS)
        self.processor = TokenManager()
        self.whale_tracker = WhaleTracker()
        self.whale_subscription = WhaleSubscription()
        
    async def process_pumped_tokens(self, pumped_tokens):
        """Process pumped tokens and track their whales"""
        if not pumped_tokens:
            return

        for token in pumped_tokens:
            token_address = token.get('contract')
            if token_address:
                logger.info(f"Analyzing whales for pumped token: {token_address}")
                wealthy_holders = await self.whale_tracker.analyze_token(token_address)
                
                if wealthy_holders:
                    logger.info(f"Found {len(wealthy_holders)} whale addresses for token {token_address}")
                    # Add these addresses to whale subscription
                    await self.whale_subscription.add_addresses(wealthy_holders)

    async def start(self):
        # Set up file system monitoring
        event_handler = DataFileHandler(
            self.processor,
            self.whale_tracker,
            self.loop
        )
        observer = Observer()
        observer.schedule(event_handler, settings.RAW_DATA_FILEPATH, recursive=False)
        observer.start()
        
        try:
            # Start data collection
            collector_task = asyncio.create_task(self.collector.collect_data())
            
            # Start whale subscription
            subscription_task = asyncio.create_task(
                self.whale_subscription.subscribe_to_transactions()
            )
            
            # Wait for both tasks
            await asyncio.gather(collector_task, subscription_task)
            
        except Exception as e:
            logger.error(f"Error in orchestrator: {e}")
            raise
            
async def main():
    orchestrator = Orchestrator()
    await orchestrator.start()

if __name__ == "__main__":
    asyncio.run(main())