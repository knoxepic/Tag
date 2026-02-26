from telethon import TelegramClient, events
import asyncio
import os
import sys

# ==============================================
# IMPORTANT: Environment Variables ya direct values
# ==============================================

# METHOD 1: Environment Variables se lena (Render me set karo)
api_id = int(os.environ.get('API_ID', 0))
api_hash = os.environ.get('API_HASH', '')
bot_token = os.environ.get('BOT_TOKEN', '')

# METHOD 2: Direct values dalo (Agar environment variables kaam nahi kar rahe)
# API_ID = 28761567          # Apna actual ID
# API_HASH = "b6320c0cc62a97d3a7d4e3055e6b9e0d"  # Apna actual hash
# BOT_TOKEN = "7798323410:AAEr5G-_15rq1H1QTTz7sWjSpEaLzN_7tuU"  # Apna actual token

# Check karo ki values hain ya nahi
if api_id == 0 or not api_hash or not bot_token:
    print("⚠️ Environment variables not found! Using direct values...")
    # Yahan direct values dalo (comment hatao)
    # api_id = API_ID
    # api_hash = API_HASH
    # bot_token = BOT_TOKEN

print(f"🚀 Starting mention bot with Python {sys.version}")
print(f"🔧 API_ID: {api_id}")
print(f"🔧 API_HASH: {api_hash[:5]}...{api_hash[-5:] if len(api_hash) > 10 else ''}")
print(f"🔧 BOT_TOKEN: {bot_token[:10]}...")

# Global client
client = None

async def main_async():
    """Async main function"""
    global client
    try:
        # Final check
        if not api_id or not api_hash or not bot_token:
            print("❌ API_ID, API_HASH, or BOT_TOKEN is missing!")
            return
        
        print("🔄 Connecting to Telegram...")
        client = TelegramClient('bot_session', api_id, api_hash)
        await client.start(bot_token=bot_token)
        
        me = await client.get_me()
        print(f"✅ Bot started: @{me.username} ({me.first_name})")
        
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
        
        print("✅ Bot is running. Press Ctrl+C to stop.")
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            await client.disconnect()

def main():
    """Main function"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        # Keep alive for Render
        import time
        time.sleep(5)
        print("🔄 Restarting...")
        main()

if __name__ == "__main__":
    main()
