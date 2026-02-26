from telethon import TelegramClient, events
import asyncio
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Environment variables
api_id = int(os.environ.get('API_ID', 28761567))
api_hash = os.environ.get('API_HASH', 'b6320c0cc62a97d3a7d4e3055e6b9e0d')
bot_token = os.environ.get('BOT_TOKEN', '7798323410:AAEr5G-_15rq1H1QTTz7sWjSpEaLzN_7tuU')

print(f"🚀 Starting mention bot with Python {sys.version}")
print(f"🔧 API_ID: {api_id}")
print(f"🔧 BOT_TOKEN: {bot_token[:10]}...")

# Simple HTTP server for Render port detection
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        # Suppress log messages
        pass

def run_http_server():
    """Run a simple HTTP server on port 10000"""
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
    print(f"📡 Health check server running on port 10000")
    server.serve_forever()

# Start HTTP server in background thread
http_thread = threading.Thread(target=run_http_server, daemon=True)
http_thread.start()

# Telegram Bot Code
client = None

async def main_async():
    global client
    try:
        print("🔄 Connecting to Telegram...")
        client = TelegramClient('bot_session', api_id, api_hash)
        await client.start(bot_token=bot_token)
        
        me = await client.get_me()
        print(f"✅ Bot started: @{me.username}")
        
        # Admin list - yahan apne aur admins ke IDs daalein
        ADMIN_IDS = [28761567, 123456789]  # Apni user ID daalein
        
        @client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            help_text = """
👋 **Group Mention Bot**

**Commands:**
• `/tagall` - Saare members ko mention karein (Admin only)
• `/adminhelp` - Admin commands
• `/help` - Ye help message

Bot ko group me admin banana zaroori hai!
            """
            await event.reply(help_text)
        
        @client.on(events.NewMessage(pattern='/adminhelp'))
        async def adminhelp_handler(event):
            if event.sender_id in ADMIN_IDS:
                admin_text = """
👑 **Admin Commands:**
• `/tagall` - Saare members ko mention karein
• `/adminlist` - Admin list dekhein
• `/addadmin [user_id]` - Naya admin add karein
• `/removeadmin [user_id]` - Admin hataein
• `/broadcast [message]` - Saare groups me message bhejein
                """
                await event.reply(admin_text)
            else:
                await event.reply("❌ Ye command sirf admin ke liye hai!")
        
        @client.on(events.NewMessage(pattern='/tagall'))
        async def tagall_handler(event):
            # Check if user is admin
            if event.sender_id not in ADMIN_IDS:
                await event.reply("❌ Sirf admin log /tagall use kar sakte hain!")
                return
            
            if not event.is_group:
                await event.reply("⚠️ Ye command sirf groups me kaam karegi.")
                return
            
            try:
                # Check if bot is admin
                bot_me = await client.get_me()
                bot_id = bot_me.id
                chat = await event.get_chat()
                
                if not chat.admin_rights and not chat.creator:
                    await event.reply("⚠️ Mujhe pehle group me admin banaona hoga!")
                    return
                
                msg = await event.reply("🔄 Saare members ko mention kar raha hoon...")
                members = await client.get_participants(event.chat_id)
                
                mentions = ""
                count = 0
                total = 0
                
                for user in members:
                    if not user.bot and not user.deleted:
                        mention = f"[{user.first_name}](tg://user?id={user.id})"
                        
                        if count < 50:
                            mentions += mention + " "
                            count += 1
                            total += 1
                        else:
                            await event.reply(mentions)
                            mentions = mention + " "
                            count = 1
                            total += 1
                            await asyncio.sleep(2)
                
                if mentions:
                    await event.reply(mentions)
                
                await msg.delete()
                await event.reply(f"✅ {total} members ko mention kiya gaya!")
                
            except Exception as e:
                await event.reply(f"❌ Error: {str(e)}")
        
        @client.on(events.NewMessage(pattern='/addadmin'))
        async def addadmin_handler(event):
            if event.sender_id not in ADMIN_IDS:
                await event.reply("❌ Sirf admin hi admin add kar sakte hain!")
                return
            
            try:
                # Command format: /addadmin 123456789
                parts = event.message.text.split()
                if len(parts) < 2:
                    await event.reply("⚠️ Usage: /addadmin [user_id]")
                    return
                
                new_admin_id = int(parts[1])
                if new_admin_id not in ADMIN_IDS:
                    ADMIN_IDS.append(new_admin_id)
                    await event.reply(f"✅ User {new_admin_id} ko admin bana diya gaya!")
                else:
                    await event.reply("⚠️ Ye user already admin hai!")
                    
            except Exception as e:
                await event.reply(f"❌ Error: {str(e)}")
        
        @client.on(events.NewMessage(pattern='/removeadmin'))
        async def removeadmin_handler(event):
            if event.sender_id not in ADMIN_IDS:
                await event.reply("❌ Sirf admin hi admin hata sakte hain!")
                return
            
            try:
                parts = event.message.text.split()
                if len(parts) < 2:
                    await event.reply("⚠️ Usage: /removeadmin [user_id]")
                    return
                
                remove_id = int(parts[1])
                if remove_id in ADMIN_IDS and remove_id != event.sender_id:
                    ADMIN_IDS.remove(remove_id)
                    await event.reply(f"✅ User {remove_id} ko admin se hata diya gaya!")
                else:
                    await event.reply("⚠️ Ye user admin nahi hai ya apne aapko nahi hata sakte!")
                    
            except Exception as e:
                await event.reply(f"❌ Error: {str(e)}")
        
        @client.on(events.NewMessage(pattern='/adminlist'))
        async def adminlist_handler(event):
            if event.sender_id not in ADMIN_IDS:
                await event.reply("❌ Ye command sirf admin ke liye hai!")
                return
            
            admin_text = "👑 **Current Admins:**\n"
            for admin_id in ADMIN_IDS:
                try:
                    user = await client.get_entity(admin_id)
                    admin_text += f"• {user.first_name} (@{user.username or 'N/A'}) - `{admin_id}`\n"
                except:
                    admin_text += f"• Unknown User - `{admin_id}`\n"
            
            await event.reply(admin_text)
        
        @client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            help_text = """
🤖 **Group Mention Bot**

**User Commands:**
• `/help` - Ye help message

**Admin Commands:**
• `/tagall` - Saare members ko mention karein
• `/adminhelp` - Admin commands ki list
• `/adminlist` - Admins ki list dekhein
• `/addadmin [id]` - Naya admin add karein
• `/removeadmin [id]` - Admin hataein
            """
            await event.reply(help_text)
        
        print("✅ Bot is running with admin features!")
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            await client.disconnect()

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import time
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()
