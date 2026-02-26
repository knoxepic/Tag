from telethon import TelegramClient, events
import asyncio
import os

# API Details (Render environment variables se le sakte ho)
API_ID = int(os.environ.get('API_ID', 1234567))  # Default value, Render me set karna
API_HASH = os.environ.get('API_HASH', 'apna_api_hash')
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'apna_bot_token')

# Global client variable
client = None

async def main():
    global client
    try:
        # Client initialize with explicit loop
        client = TelegramClient('bot', api_id, api_hash)
        await client.start(bot_token=bot_token)
        
        print("🤖 Bot successfully started!")
        
        @client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await event.reply("👋 Main group mention bot hoon!\n/tagall se saare members ko tag kar sakte ho.")
        
        @client.on(events.NewMessage(pattern='/tagall'))
        async def tagall_handler(event):
            if not event.is_group:
                await event.reply("⚠️ Ye command sirf groups me kaam karegi.")
                return
            
            try:
                msg = await event.reply("🔄 Saare members ko mention kar raha hoon...")
                
                # Group ke members nikalna
                members = await client.get_participants(event.chat_id)
                
                mentions = ""
                count = 0
                
                for user in members:
                    if not user.bot and not user.deleted:
                        mention = f"[{user.first_name}](tg://user?id={user.id})"
                        
                        if count < 50:
                            mentions += mention + " "
                            count += 1
                        else:
                            await event.reply(mentions)
                            mentions = mention + " "
                            count = 1
                            await asyncio.sleep(2)
                
                if mentions:
                    await event.reply(mentions)
                
                await msg.delete()
                
            except Exception as e:
                await event.reply(f"❌ Error: {str(e)}")
        
        @client.on(events.NewMessage)
        async def error_handler(event):
            pass  # Ignore other messages
        
        # Client ko chalte rahne dena
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Error in main: {e}")
    finally:
        if client:
            await client.disconnect()

def run_bot():
    """Bot ko start karne ka main function"""
    try:
        # Python 3.7+ ke liye asyncio.run() use karo
        asyncio.run(main())
    except RuntimeError as e:
        # Agar already event loop hai to alag tarike se handle karo
        if 'already running' in str(e).lower():
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            print(f"❌ Runtime error: {e}")
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🚀 Starting mention bot for Render...")
    run_bot()
