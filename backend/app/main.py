import asyncio
import logging
from orchestrator import Orchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    orchestrator = Orchestrator()
    await orchestrator.start()

if __name__ == "__main__":
    asyncio.run(main())