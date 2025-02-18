from collections import defaultdict
import logging
import asyncio
from datetime import datetime
from typing import Dict, List

class SmartLogger:
    def __init__(self, name: str, batch_size: int = 10, flush_interval: int = 30):
        self.logger = logging.getLogger(name)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Separate buffers for different log levels
        self.buffers: Dict[str, List[str]] = defaultdict(list)
        self.counts: Dict[str, int] = defaultdict(int)
        
        # Start background flush task
        asyncio.create_task(self._periodic_flush())
    
    async def _periodic_flush(self):
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush_all()
    
    def _format_batch(self, level: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        messages = self.buffers[level]
        count = self.counts[level]
        
        if not messages:
            return ""
            
        header = f"\n{'='*20} {level} Batch Summary ({count} events) {'='*20}"
        footer = f"{'='*70}\n"
        
        return f"{header}\n{timestamp}\n" + "\n".join(messages) + f"\n{footer}"
    
    async def flush_all(self):
        for level in self.buffers.keys():
            if self.buffers[level]:
                batch_message = self._format_batch(level)
                if batch_message:
                    getattr(self.logger, level.lower())(batch_message)
                self.buffers[level].clear()
                self.counts[level] = 0
    
    async def _log(self, level: str, message: str):
        self.buffers[level].append(message)
        self.counts[level] += 1
        
        if len(self.buffers[level]) >= self.batch_size:
            batch_message = self._format_batch(level)
            getattr(self.logger, level.lower())(batch_message)
            self.buffers[level].clear()
            self.counts[level] = 0
    
    async def info(self, message: str):
        await self._log("INFO", message)
    
    async def warning(self, message: str):
        await self._log("WARNING", message)
    
    async def error(self, message: str):
        # Errors are logged immediately
        self.logger.error(message)
    
    async def debug(self, message: str):
        await self._log("DEBUG", message)