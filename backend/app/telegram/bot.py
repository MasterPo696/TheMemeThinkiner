import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from utils.config import settings
from parcing.subscription import WhaleSubscription

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print(settings.BOT_TOKEN)

# Initialize bot and dispatcher
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Admin user ID - replace with your Telegram user ID
ADMIN_USER_ID = "1234567890"  # Replace this with your actual Telegram ID

class WhaleAlertBot:
    def __init__(self):
        self.whale_subscription = WhaleSubscription()
        
    async def start_monitoring(self):
        """Start monitoring whale transactions and send alerts"""
        try:
            while True:
                async with self.whale_subscription.subscribe_to_transactions() as subscription:
                    async for transaction in subscription:
                        await self.process_transaction(transaction)
        except Exception as e:
            logger.error(f"Error in whale monitoring: {e}")
            await self.send_admin_alert(f"🚨 Monitoring error: {str(e)}")

    async def process_transaction(self, transaction):
        """Process incoming whale transactions and send alerts"""
        try:
            amount = transaction.get('amount', 0)
            wallet = transaction.get('wallet', 'Unknown')
            
            if amount >= settings.ALERT_AMOUNT:
                message = (
                    f"🐋 Whale Transaction Detected!\n\n"
                    f"Wallet: `{wallet}`\n"
                    f"Amount: ${amount:,.2f}\n"
                    f"Time: {transaction.get('timestamp', 'Unknown')}"
                )
                await self.send_admin_alert(message)
                
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")

    async def send_admin_alert(self, message):
        """Send alert to admin user"""
        try:
            await bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to send admin alert: {e}")

@router.message(Command("start"))
async def start_command(message: types.Message):
    """Handle /start command"""
    if str(message.from_user.id) == ADMIN_USER_ID:
        await message.reply(
            "🐋 Welcome to Whale Alert Bot!\n\n"
            "I'll notify you about significant whale transactions."
        )
    else:
        await message.reply("⚠️ This bot is for admin use only.")

@router.message(Command("status")) 
async def status_command(message: types.Message):
    """Handle /status command"""
    if str(message.from_user.id) == ADMIN_USER_ID:
        subscription = WhaleSubscription()
        whale_count = len(subscription.wealthy_holders)
        await message.reply(
            f"📊 Current Status:\n"
            f"Monitoring {whale_count} whale addresses\n"
            f"Alert threshold: ${settings.ALERT_AMOUNT:,.2f}"
        )
    else:
        await message.reply("⚠️ This command is for admin use only.")

async def main():
    """Main function to start the bot"""
    whale_bot = WhaleAlertBot()
    
    # Include router
    dp.include_router(router)
    
    # Start monitoring in background
    asyncio.create_task(whale_bot.start_monitoring())
    
    # Start the bot
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())