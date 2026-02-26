from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek
import asyncio
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import random

# ==============================================
# CONFIGURATION - APNI VALUES DALEIN
# ==============================================
api_id = int(os.environ.get('API_ID', 28761567))
api_hash = os.environ.get('API_HASH', 'b6320c0cc62a97d3a7d4e3055e6b9e0d')
bot_token = os.environ.get('BOT_TOKEN', '7798323410:AAEr5G-_15rq1H1QTTz7sWjSpEaLzN_7tuU')

# Admin IDs (apni ID dalo)
OWNER_ID = 28761567  # <-- APNI ID YAHAN DALEIN
ADMIN_IDS = [OWNER_ID]

# Emoji list for tagging
EMOJIS = ["🔥", "⭐", "💫", "✨", "🌟", "💥", "⚡", "🎯", "🎪", "🎨", "🎭", "🎪", "🎢", "🎡", "🎠"]

# File for persistent storage
ADMIN_FILE = "admins.txt"
STOP_FILE = "stop.txt"

# ==============================================
# HELPER FUNCTIONS
# ==============================================

def load_admins():
    global ADMIN_IDS
    try:
        if os.path.exists(ADMIN_FILE):
            with open(ADMIN_FILE, 'r') as f:
                ids = f.read().strip().split(',')
                if ids and ids[0]:
                    ADMIN_IDS = [int(id) for id in ids if id]
    except:
        pass
    if OWNER_ID not in ADMIN_IDS:
        ADMIN_IDS.append(OWNER_ID)
        save_admins()

def save_admins():
    try:
        with open(ADMIN_FILE, 'w') as f:
            f.write(','.join(str(id) for id in ADMIN_IDS))
    except:
        pass

def is_stopped(chat_id):
    """Check if mention is stopped for this chat"""
    try:
        if os.path.exists(STOP_FILE):
            with open(STOP_FILE, 'r') as f:
                stopped_chats = f.read().split(',')
                return str(chat_id) in stopped_chats
    except:
        pass
    return False

def set_stop(chat_id, stop=True):
    """Stop or resume mentions for a chat"""
    try:
        stopped = []
        if os.path.exists(STOP_FILE):
            with open(STOP_FILE, 'r') as f:
                stopped = f.read().split(',')
        
        chat_id_str = str(chat_id)
        if stop and chat_id_str not in stopped:
            stopped.append(chat_id_str)
        elif not stop and chat_id_str in stopped:
            stopped.remove(chat_id_str)
        
        with open(STOP_FILE, 'w') as f:
            f.write(','.join(stopped))
    except:
        pass

def get_random_emoji():
    return random.choice(EMOJIS)

# Load saved admins
load_admins()

# ==============================================
# HTTP SERVER FOR RENDER (FIXED VERSION)
# ==============================================

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # FIXED: Proper string encoding
        html_content = f'''
        <html>
            <head><title>Mention Bot</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>🤖 Telegram Mention Bot is Running!</h1>
                <p>Bot is active and working...</p>
                <p>Total Admins: {len(ADMIN_IDS)}</p>
                <p>Owner ID: {OWNER_ID}</p>
                <p>Status: ✅ Online</p>
            </body>
        </html>
        '''
        self.wfile.write(html_content.encode())
    
    def log_message(self, format, *args):
        pass

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
    print(f"📡 Health check server running on port 10000")
    server.serve_forever()

# Start HTTP server
http_thread = threading.Thread(target=run_http_server, daemon=True)
http_thread.start()

# ==============================================
# TELEGRAM BOT
# ==============================================

client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

async def is_admin(user_id):
    return user_id in ADMIN_IDS

async def send_mention(event, users, custom_text="", use_emoji=True):
    """Send mentions with optional text and emoji"""
    mentions = ""
    count = 0
    total = 0
    
    bot_me = await client.get_me()
    
    for user in users:
        if not user.bot and not user.deleted and user.id != bot_me.id:
            if use_emoji:
                emoji = get_random_emoji()
                mention = f"[{emoji}](tg://user?id={user.id})"
            else:
                mention = f"[‎](tg://user?id={user.id})"  # Invisible character
            
            if count < 50:
                mentions += mention + " "
                count += 1
                total += 1
            else:
                if custom_text:
                    await event.reply(f"{custom_text}\n\n{mentions}")
                else:
                    await event.reply(mentions)
                mentions = mention + " "
                count = 1
                total += 1
                await asyncio.sleep(2)
    
    if mentions:
        if custom_text:
            await event.reply(f"{custom_text}\n\n{mentions}")
        else:
            await event.reply(mentions)
    
    return total

# ==============================================
# BOT COMMANDS
# ==============================================

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Welcome message"""
    user_id = event.sender_id
    is_admin_user = await is_admin(user_id)
    
    welcome_msg = f"""
🌟 **Welcome to Mention Bot!** 🌟

👋 Hello {event.sender.first_name}!

**Your Status:** {'👑 ADMIN' if is_admin_user else '👤 USER'}
**Your ID:** `{user_id}`

**📋 Available Commands:**

🔹 **For Everyone:**
• `/help` - Show all commands
• `/id` - Get your user ID

🔹 **Mention Commands:**
• `@all` or `/tagall` - Mention all members
• `/hello [message]` - Mention with your message
• `/online` - Mention online members only

🔹 **Admin Commands:**
• `/admins` - Mention only admins
• `/broadcast [msg]` - Broadcast to all groups

**📌 Note:** Bot ko group me admin banana zaroori hai!

**🤖 Status:** Bot is active and working!
"""
    await event.reply(welcome_msg)

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Help command"""
    user_id = event.sender_id
    is_admin_user = await is_admin(user_id)
    
    help_text = f"""
📚 **MENTION BOT COMMANDS**

**👤 USER COMMANDS:**
━━━━━━━━━━━━━━━━
• `/start` - Welcome message
• `/help` - Show this help
• `/id` - Show your user ID
• `@all` or `/tagall` - Mention everyone
• `/hello [msg]` - Mention with custom message
• `/online` - Mention online users only

**👑 ADMIN COMMANDS:**
━━━━━━━━━━━━━━━━
• `/admins` - Mention all admins
• `/addadmin [id]` - Add new admin
• `/removeadmin [id]` - Remove admin
• `/adminlist` - List all admins
• `/broadcast [msg]` - Message all groups
• `/stop` - Stop mentions in this group
• `/resume` - Resume mentions
• `/stats` - Bot statistics

**✨ FEATURES:**
━━━━━━━━━━━━━━━━
• ✅ Auto detects group/user
• ✅ Emoji based mentions
• ✅ Online user detection
• ✅ Admin only commands
• ✅ Broadcast feature
• ✅ Stop/Resume mentions

**Your Status:** {'👑 ADMIN' if is_admin_user else '👤 USER'}
**Your ID:** `{user_id}`
"""
    await event.reply(help_text)

@client.on(events.NewMessage(pattern='/id'))
async def id_handler(event):
    """Show user ID"""
    user_id = event.sender_id
    chat = event.chat
    chat_type = "Group" if event.is_group else "Private"
    
    await event.reply(f"""
🆔 **Your Information**
━━━━━━━━━━━━━━━━
**User ID:** `{user_id}`
**Username:** @{event.sender.username or 'N/A'}
**First Name:** {event.sender.first_name}
**Chat Type:** {chat_type}
**Chat ID:** `{chat.id if event.is_group else 'Private'}`
**Admin:** {'✅ Yes' if await is_admin(user_id) else '❌ No'}
""")

@client.on(events.NewMessage(pattern='@all'))
@client.on(events.NewMessage(pattern='/tagall'))
async def tagall_handler(event):
    """Mention all members"""
    if not event.is_group:
        await event.reply("⚠️ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply(f"❌ Only admins can use this command!\nYour ID: `{user_id}`")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⚠️ Mentions are stopped in this group. Use /resume to start again.")
        return
    
    try:
        msg = await event.reply("🔄 Fetching members and preparing mentions...")
        members = await client.get_participants(event.chat_id)
        
        total = await send_mention(event, members, use_emoji=True)
        
        await msg.delete()
        await event.reply(f"✅ {total} members mentioned with emojis!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/hello'))
async def hello_handler(event):
    """Mention with custom message"""
    if not event.is_group:
        await event.reply("⚠️ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply(f"❌ Only admins can use this command!")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⚠️ Mentions are stopped in this group. Use /resume to start again.")
        return
    
    try:
        # Extract custom message
        custom_text = event.message.text.replace('/hello', '', 1).strip()
        if not custom_text:
            custom_text = "Hello everyone! 👋"
        
        msg = await event.reply("🔄 Preparing mentions with your message...")
        members = await client.get_participants(event.chat_id)
        
        total = await send_mention(event, members, custom_text, use_emoji=True)
        
        await msg.delete()
        await event.reply(f"✅ {total} members mentioned with message: {custom_text}")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/online'))
async def online_handler(event):
    """Mention only online members"""
    if not event.is_group:
        await event.reply("⚠️ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply(f"❌ Only admins can use this command!")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⚠️ Mentions are stopped in this group. Use /resume to start again.")
        return
    
    try:
        msg = await event.reply("🔄 Finding online members...")
        members = await client.get_participants(event.chat_id)
        
        online_users = []
        for user in members:
            if not user.bot and not user.deleted:
                if hasattr(user, 'status') and isinstance(user.status, UserStatusOnline):
                    online_users.append(user)
        
        if not online_users:
            await event.reply("😴 No online members found!")
            await msg.delete()
            return
        
        total = await send_mention(event, online_users, "🟢 **Online Members:**", use_emoji=True)
        
        await msg.delete()
        await event.reply(f"✅ {total} online members mentioned!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/admins'))
async def admins_handler(event):
    """Mention only admins"""
    if not event.is_group:
        await event.reply("⚠️ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply(f"❌ Only admins can use this command!")
        return
    
    try:
        msg = await event.reply("🔄 Fetching admins...")
        chat = await event.get_chat()
        
        members = await client.get_participants(event.chat_id)
        admins = []
        
        for user in members:
            if hasattr(user, 'admin_rights') and user.admin_rights:
                admins.append(user)
            elif hasattr(chat, 'creator_id') and user.id == chat.creator_id:
                admins.append(user)
        
        if not admins:
            await event.reply("No admins found!")
            await msg.delete()
            return
        
        total = await send_mention(event, admins, "👑 **Group Admins:**", use_emoji=True)
        
        await msg.delete()
        await event.reply(f"✅ {total} admins mentioned!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_handler(event):
    """Broadcast message to all groups"""
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply("❌ Only admins can use broadcast!")
        return
    
    try:
        # Extract broadcast message
        broadcast_msg = event.message.text.replace('/broadcast', '', 1).strip()
        if not broadcast_msg:
            await event.reply("⚠️ Please provide a message!\nExample: `/broadcast Hello everyone!`")
            return
        
        msg = await event.reply("📢 Broadcasting to all groups...")
        
        # Get all dialogs (chats)
        dialogs = await client.get_dialogs()
        groups = [dialog for dialog in dialogs if dialog.is_group]
        
        success = 0
        failed = 0
        
        for group in groups:
            try:
                await client.send_message(group.id, f"📢 **Broadcast Message**\n\n{broadcast_msg}")
                success += 1
                await asyncio.sleep(1)  # Delay to avoid flooding
            except:
                failed += 1
        
        await msg.delete()
        await event.reply(f"✅ Broadcast complete!\n\n📨 Sent to: {success} groups\n❌ Failed: {failed} groups")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/stop'))
async def stop_handler(event):
    """Stop mentions in this group"""
    if not event.is_group:
        await event.reply("⚠️ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply("❌ Only admins can stop mentions!")
        return
    
    set_stop(event.chat_id, True)
    await event.reply("⏸️ Mentions stopped in this group. Use /resume to start again.")

@client.on(events.NewMessage(pattern='/resume'))
async def resume_handler(event):
    """Resume mentions in this group"""
    if not event.is_group:
        await event.reply("⚠️ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply("❌ Only admins can resume mentions!")
        return
    
    set_stop(event.chat_id, False)
    await event.reply("▶️ Mentions resumed in this group!")

@client.on(events.NewMessage(pattern='/addadmin'))
async def addadmin_handler(event):
    """Add new admin"""
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply("❌ Only admins can add new admins!")
        return
    
    try:
        parts = event.message.text.split()
        if len(parts) < 2:
            await event.reply("⚠️ Usage: `/addadmin [user_id]`")
            return
        
        new_admin_id = int(parts[1])
        
        if new_admin_id in ADMIN_IDS:
            await event.reply("⚠️ This user is already an admin!")
            return
        
        ADMIN_IDS.append(new_admin_id)
        save_admins()
        
        await event.reply(f"✅ User `{new_admin_id}` added as admin!\n\nTotal admins: {len(ADMIN_IDS)}")
        
    except ValueError:
        await event.reply("❌ Invalid user ID! Must be a number.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/removeadmin'))
async def removeadmin_handler(event):
    """Remove admin"""
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply("❌ Only admins can remove admins!")
        return
    
    try:
        parts = event.message.text.split()
        if len(parts) < 2:
            await event.reply("⚠️ Usage: `/removeadmin [user_id]`")
            return
        
        remove_id = int(parts[1])
        
        if remove_id == OWNER_ID:
            await event.reply("❌ Cannot remove the owner!")
            return
        
        if remove_id not in ADMIN_IDS:
            await event.reply("⚠️ This user is not an admin!")
            return
        
        ADMIN_IDS.remove(remove_id)
        save_admins()
        
        await event.reply(f"✅ User `{remove_id}` removed from admins!\n\nTotal admins: {len(ADMIN_IDS)}")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/adminlist'))
async def adminlist_handler(event):
    """List all admins"""
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
    admin_text += f"\nYour Status: {'✅ Admin' if await is_admin(user_id) else '❌ Not Admin'}"
    
    await event.reply(admin_text)

@client.on(events.NewMessage(pattern='/stats'))
async def stats_handler(event):
    """Bot statistics"""
    user_id = event.sender_id
    
    try:
        dialogs = await client.get_dialogs()
        groups = [d for d in dialogs if d.is_group]
        users = [d for d in dialogs if d.is_user and not d.entity.bot]
        
        stats_text = f"""
📊 **Bot Statistics**

**📁 Groups:**
• Total Groups: {len(groups)}

**👥 Users:**
• Total Users: {len(users)}
• Admins: {len(ADMIN_IDS)}

**🤖 Bot Info:**
• Uptime: Active
• Version: 2.0
• Owner: `{OWNER_ID}`

**Your Status:**
• ID: `{user_id}`
• Admin: {'✅ Yes' if await is_admin(user_id) else '❌ No'}
"""
        await event.reply(stats_text)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage)
async def message_handler(event):
    """Auto detect group/user"""
    if event.is_group:
        # Group message detected
        chat_title = event.chat.title if hasattr(event.chat, 'title') else "Unknown"
        print(f"📢 Group message in: {chat_title} (ID: {event.chat_id})")
    
    elif event.is_private:
        # Private message detected
        user = event.sender
        print(f"💬 Private message from: {user.first_name} (ID: {user.id})")

# ==============================================
# START BOT
# ==============================================

print("🚀 Starting Mention Bot...")
print(f"👑 Owner ID: {OWNER_ID}")
print(f"👑 Admins: {ADMIN_IDS}")
print("✅ Bot is running! Press Ctrl+C to stop.")

try:
    client.run_until_disconnected()
except KeyboardInterrupt:
    print("\n👋 Bot stopped by user")
except Exception as e:
    print(f"❌ Error: {e}")
