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

# ==============================================
# IMPORTANT: APNI USER ID YAHAN DALEIN
# ==============================================
# @userinfobot se apni ID nikal kar yahan daalein
MY_USER_ID = 7957361876  # <-- YAHAN APNI ACTUAL USER ID DALEIN

# Admin list - initially sirf aap
ADMIN_IDS = [MY_USER_ID]

# File to store admin list (persistent storage)
ADMIN_FILE = "admins.txt"

def load_admins():
    """Save ki hui admin list load karein"""
    global ADMIN_IDS
    try:
        if os.path.exists(ADMIN_FILE):
            with open(ADMIN_FILE, 'r') as f:
                ids = f.read().strip().split(',')
                if ids and ids[0]:
                    ADMIN_IDS = [int(id) for id in ids if id]
                    print(f"📂 Loaded admins: {ADMIN_IDS}")
    except Exception as e:
        print(f"⚠️ Error loading admins: {e}")
    
    # Ensure MY_USER_ID is always admin
    if MY_USER_ID not in ADMIN_IDS:
        ADMIN_IDS.append(MY_USER_ID)
        save_admins()

def save_admins():
    """Admin list save karein"""
    try:
        with open(ADMIN_FILE, 'w') as f:
            f.write(','.join(str(id) for id in ADMIN_IDS))
    except Exception as e:
        print(f"⚠️ Error saving admins: {e}")

# Load saved admins
load_admins()
print(f"👑 Current admins: {ADMIN_IDS}")

# Simple HTTP server for Render port detection
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        pass  # Suppress log messages

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

async def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def main_async():
    global client, ADMIN_IDS
    try:
        print("🔄 Connecting to Telegram...")
        client = TelegramClient('bot_session', api_id, api_hash)
        await client.start(bot_token=bot_token)
        
        me = await client.get_me()
        print(f"✅ Bot started: @{me.username} (ID: {me.id})")
        print(f"👑 Your user ID: {MY_USER_ID}")
        print(f"👑 Admin IDs: {ADMIN_IDS}")
        
        @client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            user_id = event.sender_id
            admin_status = "✅ (Admin)" if await is_admin(user_id) else "❌ (Not Admin)"
            
            help_text = f"""
👋 **Group Mention Bot**

Your ID: `{user_id}` {admin_status}

**Commands:**
• `/tagall` - Saare members ko mention karein (Admin only)
• `/adminhelp` - Admin commands (Admin only)
• `/myid` - Apni ID dekhein
• `/help` - Ye help message

Bot ko group me admin banana zaroori hai!
            """
            await event.reply(help_text)
        
        @client.on(events.NewMessage(pattern='/myid'))
        async def myid_handler(event):
            user_id = event.sender_id
            admin_status = "Admin" if await is_admin(user_id) else "Normal User"
            await event.reply(f"🆔 Your Telegram ID: `{user_id}`\nStatus: {admin_status}")
        
        @client.on(events.NewMessage(pattern='/adminhelp'))
        async def adminhelp_handler(event):
            user_id = event.sender_id
            if not await is_admin(user_id):
                await event.reply(f"❌ Sirf admin ye command use kar sakte hain!\nYour ID: `{user_id}` (Not in admin list: {ADMIN_IDS})")
                return
            
            admin_text = f"""
👑 **Admin Commands:**
• `/tagall` - Saare members ko mention karein
• `/adminlist` - Admin list dekhein
• `/addadmin [user_id]` - Naya admin add karein
• `/removeadmin [user_id]` - Admin hataein
• `/admins` - Current admins ki list

Your ID: `{user_id}` is in admin list ✅
            """
            await event.reply(admin_text)
        
        @client.on(events.NewMessage(pattern='/tagall'))
        async def tagall_handler(event):
            user_id = event.sender_id
            
            # Detailed admin check with debug info
            is_admin_user = await is_admin(user_id)
            print(f"🔍 /tagall used by user {user_id}, is_admin: {is_admin_user}, admin_list: {ADMIN_IDS}")
            
            if not is_admin_user:
                await event.reply(
                    f"❌ Sirf admin log /tagall use kar sakte hain!\n\n"
                    f"Your ID: `{user_id}`\n"
                    f"Admin IDs: `{ADMIN_IDS}`\n\n"
                    f"Apni ID @userinfobot se check karein aur admin se add karayein."
                )
                return
            
            if not event.is_group:
                await event.reply("⚠️ Ye command sirf groups me kaam karegi.")
                return
            
            try:
                # Check if bot is admin
                chat = await event.get_chat()
                bot_me = await client.get_me()
                
                if not chat.admin_rights and not chat.creator:
                    await event.reply("⚠️ Mujhe pehle group me admin banana hoga!")
                    return
                
                msg = await event.reply("🔄 Saare members ko mention kar raha hoon...")
                members = await client.get_participants(event.chat_id)
                
                mentions = ""
                count = 0
                total = 0
                
                for user in members:
                    if not user.bot and not user.deleted:
                        name = user.first_name or "User"
                        mention = f"[{name}](tg://user?id={user.id})"
                        
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
            user_id = event.sender_id
            
            if not await is_admin(user_id):
                await event.reply(f"❌ Sirf admin hi admin add kar sakte hain!\nYour ID: `{user_id}`")
                return
            
            try:
                parts = event.message.text.split()
                if len(parts) < 2:
                    await event.reply("⚠️ Usage: /addadmin [user_id]\nExample: /addadmin 123456789")
                    return
                
                new_admin_id = int(parts[1])
                
                if new_admin_id in ADMIN_IDS:
                    await event.reply(f"⚠️ User {new_admin_id} already admin hai!")
                    return
                
                ADMIN_IDS.append(new_admin_id)
                save_admins()
                
                # Try to get user info
                try:
                    user = await client.get_entity(new_admin_id)
                    name = user.first_name
                except:
                    name = "Unknown"
                
                await event.reply(f"✅ {name} (ID: {new_admin_id}) ko admin bana diya gaya!\nCurrent admins: {ADMIN_IDS}")
                
            except ValueError:
                await event.reply("❌ Invalid user ID! Sirf numbers dalein.")
            except Exception as e:
                await event.reply(f"❌ Error: {str(e)}")
        
        @client.on(events.NewMessage(pattern='/removeadmin'))
        async def removeadmin_handler(event):
            user_id = event.sender_id
            
            if not await is_admin(user_id):
                await event.reply(f"❌ Sirf admin hi admin hata sakte hain!\nYour ID: `{user_id}`")
                return
            
            try:
                parts = event.message.text.split()
                if len(parts) < 2:
                    await event.reply("⚠️ Usage: /removeadmin [user_id]")
                    return
                
                remove_id = int(parts[1])
                
                if remove_id == MY_USER_ID:
                    await event.reply("❌ Main admin (creator) ko nahi hata sakte!")
                    return
                
                if remove_id not in ADMIN_IDS:
                    await event.reply(f"⚠️ User {remove_id} admin list mein nahi hai!")
                    return
                
                ADMIN_IDS.remove(remove_id)
                save_admins()
                
                await event.reply(f"✅ User {remove_id} ko admin se hata diya gaya!\nCurrent admins: {ADMIN_IDS}")
                
            except Exception as e:
                await event.reply(f"❌ Error: {str(e)}")
        
        @client.on(events.NewMessage(pattern='/adminlist'))
        @client.on(events.NewMessage(pattern='/admins'))
        async def adminlist_handler(event):
            user_id = event.sender_id
            
            admin_text = "👑 **Current Admins:**\n\n"
            
            for admin_id in ADMIN_IDS:
                try:
                    user = await client.get_entity(admin_id)
                    name = user.first_name or "Unknown"
                    username = f"@{user.username}" if user.username else "No username"
                    admin_text += f"• {name} ({username}) - `{admin_id}`\n"
                except:
                    admin_text += f"• Unknown User - `{admin_id}`\n"
            
            admin_text += f"\nTotal: {len(ADMIN_IDS)} admins"
            admin_text += f"\n\nYour ID: `{user_id}`"
            
            await event.reply(admin_text)
        
        @client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            user_id = event.sender_id
            admin_status = "✅ (Admin)" if await is_admin(user_id) else "❌ (Not Admin)"
            
            help_text = f"""
🤖 **Group Mention Bot**

Your Status: {admin_status}
Your ID: `{user_id}`

**User Commands:**
• `/help` - Ye help message
• `/myid` - Apni ID dekhein

**Admin Commands:**
• `/tagall` - Saare members ko mention karein
• `/adminhelp` - Admin commands ki list
• `/admins` - Admins ki list dekhein
• `/addadmin [id]` - Naya admin add karein
• `/removeadmin [id]` - Admin hataein

**Note:** Bot ko group me admin banana zaroori hai!
            """
            await event.reply(help_text)
        
        print("✅ Bot is running with admin features!")
        print(f"👑 Your admin ID: {MY_USER_ID}")
        print(f"👑 All admins: {ADMIN_IDS}")
        
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
