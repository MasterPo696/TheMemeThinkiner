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
        await self.processor.process_latest_raw_data()
        
        # After finding pumped tokens, analyze for whales
        await self.whale_tracker.main()

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
        self.whale_tracker = WhaleTracker(settings.SOLANA_RPC)
        self.whale_subscription = WhaleSubscription()
        
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
            logger.error(f"Error in orchestration: {e}")
        finally:
            observer.stop()
            observer.join()
            
async def main():
    orchestrator = Orchestrator()
    await orchestrator.start()

if __name__ == "__main__":
    asyncio.run(main())