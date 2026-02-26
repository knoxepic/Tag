from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline
import asyncio
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import random
import re

# ==============================================
# CONFIGURATION - APNI VALUES DALEIN
# ==============================================
api_id = int(os.environ.get('API_ID', 28761567))
api_hash = os.environ.get('API_HASH', 'b6320c0cc62a97d3a7d4e3055e6b9e0d')
bot_token = os.environ.get('BOT_TOKEN', '7798323410:AAEr5G-_15rq1H1QTTz7sWjSpEaLzN_7tuU')

# ==============================================
# IMPORTANT: APNI USER ID YAHAN DALEIN
# ==============================================
# @userinfobot se apni ID nikal kar yahan daalein
OWNER_ID = 7957361876  # <-- YAHAN APNI ACTUAL USER ID DALEIN

# Admin list - initially sirf aap
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
    print(f"📂 Loaded admins: {ADMIN_IDS}")

def save_admins():
    try:
        with open(ADMIN_FILE, 'w') as f:
            f.write(','.join(str(id) for id in ADMIN_IDS))
    except:
        pass

def is_stopped(chat_id):
    try:
        if os.path.exists(STOP_FILE):
            with open(STOP_FILE, 'r') as f:
                stopped_chats = f.read().split(',')
                return str(chat_id) in stopped_chats
    except:
        pass
    return False

def set_stop(chat_id, stop=True):
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
# HTTP SERVER FOR RENDER
# ==============================================

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
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
    """Check if user is admin - FIXED VERSION"""
    result = user_id in ADMIN_IDS
    print(f"🔍 Admin check: User {user_id} is admin? {result} (Admin list: {ADMIN_IDS})")
    return result

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
                mention = f"[‎](tg://user?id={user.id})"
            
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

**Your Information:**
• Your ID: `{user_id}`
• Status: {'👑 ADMIN' if is_admin_user else '👤 USER'}
• Bot Owner: `{OWNER_ID}`

**📋 Available Commands:**

🔹 **For Everyone:**
• `/help` - Show all commands
• `/id` - Get your user ID
• `/myid` - Apni ID dekhein

🔹 **Mention Commands (Admin Only):**
• `@all` - Mention all members
• `@tagall` - Mention all members
• `/tagall` - Mention all members
• `/all` - Mention all members
• `/hello [message]` - Mention with your message
• `/online` - Mention online members only
• `/admins` - Mention only admins

🔹 **Admin Commands:**
• `/addadmin [id]` - Naya admin add
• `/removeadmin [id]` - Admin hatao
• `/adminlist` - Admin list dekho
• `/broadcast [msg]` - Sab groups mein message bhejo
• `/stop` - Mentions band karo
• `/resume` - Mentions resume karo
• `/stats` - Bot statistics

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

**👤 YOUR INFO:**
━━━━━━━━━━━━━━━━
• Your ID: `{user_id}`
• Status: {'👑 ADMIN' if is_admin_user else '👤 USER'}
• Owner ID: `{OWNER_ID}`

**👤 USER COMMANDS:**
━━━━━━━━━━━━━━━━
• `/start` - Welcome message
• `/help` - Show this help
• `/id` or `/myid` - Show your user ID

**👑 MENTION COMMANDS (Admin Only):**
━━━━━━━━━━━━━━━━
• `@all` - Mention everyone
• `@tagall` - Mention everyone
• `/tagall` - Mention everyone
• `/all` - Mention everyone
• `/hello [msg]` - Mention with custom message
• `/online` - Mention online users only
• `/admins` - Mention all admins

**👑 ADMIN MANAGEMENT:**
━━━━━━━━━━━━━━━━
• `/addadmin [id]` - Add new admin
• `/removeadmin [id]` - Remove admin
• `/adminlist` - List all admins

**👑 GROUP MANAGEMENT:**
━━━━━━━━━━━━━━━━
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
"""
    await event.reply(help_text)

@client.on(events.NewMessage(pattern='/id'))
@client.on(events.NewMessage(pattern='/myid'))
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
**Admin Status:** {'✅ Yes' if await is_admin(user_id) else '❌ No'}
**Owner ID:** `{OWNER_ID}`
""")

# ==============================================
# ALL MENTION COMMANDS - Ek hi handler mein sab
# ==============================================
@client.on(events.NewMessage(pattern=r'^@all$|^@tagall$|^/tagall$|^/all$'))
async def tagall_handler(event):
    """Mention all members - Works with @all, @tagall, /tagall, /all"""
    
    # Debug info
    print(f"📢 Command received: {event.message.text} from user {event.sender_id}")
    
    if not event.is_group:
        await event.reply("⚠️ Yeh command sirf groups mein kaam karti hai!")
        return
    
    user_id = event.sender_id
    
    # Admin check with detailed debug
    is_admin_user = await is_admin(user_id)
    print(f"🔍 Admin check result: {is_admin_user}")
    
    if not is_admin_user:
        await event.reply(
            f"❌ Sirf admin log yeh command use kar sakte hain!\n\n"
            f"**Your ID:** `{user_id}`\n"
            f"**Admin IDs:** `{ADMIN_IDS}`\n"
            f"**Owner ID:** `{OWNER_ID}`\n\n"
            f"📌 **Solution:**\n"
            f"1. `/myid` se apni ID check karein\n"
            f"2. Agar aap owner hain to `OWNER_ID` code mein sahi daalein\n"
            f"3. Ya kisi admin se `/addadmin {user_id}` karayein"
        )
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⚠️ Mentions is group mein band hain. /resume se chalu karein.")
        return
    
    try:
        msg = await event.reply("🔄 Members fetch kar raha hoon...")
        members = await client.get_participants(event.chat_id)
        
        total = await send_mention(event, members, use_emoji=True)
        
        await msg.delete()
        await event.reply(f"✅ {total} members ko emoji ke saath mention kiya gaya!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ==============================================
# OTHER COMMANDS
# ==============================================

@client.on(events.NewMessage(pattern='/hello'))
async def hello_handler(event):
    """Mention with custom message"""
    if not event.is_group:
        await event.reply("⚠️ Yeh command sirf groups mein kaam karti hai!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply(f"❌ Sirf admin log yeh command use kar sakte hain!\nYour ID: `{user_id}`")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⚠️ Mentions is group mein band hain. /resume se chalu karein.")
        return
    
    try:
        custom_text = event.message.text.replace('/hello', '', 1).strip()
        if not custom_text:
            custom_text = "Hello everyone! 👋"
        
        msg = await event.reply("🔄 Mentions prepare kar raha hoon...")
        members = await client.get_participants(event.chat_id)
        
        total = await send_mention(event, members, custom_text, use_emoji=True)
        
        await msg.delete()
        await event.reply(f"✅ {total} members ko mention kiya: {custom_text}")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/online'))
async def online_handler(event):
    """Mention only online members"""
    if not event.is_group:
        await event.reply("⚠️ Yeh command sirf groups mein kaam karti hai!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply(f"❌ Sirf admin log yeh command use kar sakte hain!")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⚠️ Mentions is group mein band hain. /resume se chalu karein.")
        return
    
    try:
        msg = await event.reply("🔄 Online members dhundh raha hoon...")
        members = await client.get_participants(event.chat_id)
        
        online_users = []
        for user in members:
            if not user.bot and not user.deleted:
                if hasattr(user, 'status') and isinstance(user.status, UserStatusOnline):
                    online_users.append(user)
        
        if not online_users:
            await event.reply("😴 Koi online member nahi mila!")
            await msg.delete()
            return
        
        total = await send_mention(event, online_users, "🟢 **Online Members:**", use_emoji=True)
        
        await msg.delete()
        await event.reply(f"✅ {total} online members ko mention kiya!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/admins'))
async def admins_handler(event):
    """Mention only admins"""
    if not event.is_group:
        await event.reply("⚠️ Yeh command sirf groups mein kaam karti hai!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply(f"❌ Sirf admin log yeh command use kar sakte hain!")
        return
    
    try:
        msg = await event.reply("🔄 Admins dhundh raha hoon...")
        members = await client.get_participants(event.chat_id)
        
        admins = []
        chat = await event.get_chat()
        
        for user in members:
            if not user.bot and not user.deleted:
                if hasattr(user, 'admin_rights') and user.admin_rights:
                    admins.append(user)
                elif hasattr(chat, 'creator_id') and user.id == chat.creator_id:
                    admins.append(user)
        
        if not admins:
            await event.reply("Koi admin nahi mila!")
            await msg.delete()
            return
        
        total = await send_mention(event, admins, "👑 **Group Admins:**", use_emoji=True)
        
        await msg.delete()
        await event.reply(f"✅ {total} admins ko mention kiya!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/addadmin'))
async def addadmin_handler(event):
    """Add new admin"""
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply(f"❌ Sirf admin log naye admin add kar sakte hain!\nYour ID: `{user_id}`")
        return
    
    try:
        parts = event.message.text.split()
        if len(parts) < 2:
            await event.reply("⚠️ Usage: `/addadmin [user_id]`\nExample: `/addadmin 123456789`")
            return
        
        new_admin_id = int(parts[1])
        
        if new_admin_id in ADMIN_IDS:
            await event.reply(f"⚠️ User `{new_admin_id}` already admin hai!")
            return
        
        ADMIN_IDS.append(new_admin_id)
        save_admins()
        
        await event.reply(f"✅ User `{new_admin_id}` ko admin bana diya gaya!\n\nTotal admins: {len(ADMIN_IDS)}\nAdmins: {ADMIN_IDS}")
        
    except ValueError:
        await event.reply("❌ Invalid user ID! Sirf numbers daalein.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/removeadmin'))
async def removeadmin_handler(event):
    """Remove admin"""
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply("❌ Sirf admin log admin hata sakte hain!")
        return
    
    try:
        parts = event.message.text.split()
        if len(parts) < 2:
            await event.reply("⚠️ Usage: `/removeadmin [user_id]`")
            return
        
        remove_id = int(parts[1])
        
        if remove_id == OWNER_ID:
            await event.reply("❌ Owner ko nahi hata sakte!")
            return
        
        if remove_id not in ADMIN_IDS:
            await event.reply(f"⚠️ User `{remove_id}` admin nahi hai!")
            return
        
        ADMIN_IDS.remove(remove_id)
        save_admins()
        
        await event.reply(f"✅ User `{remove_id}` ko admin se hata diya!\n\nTotal admins: {len(ADMIN_IDS)}")
        
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
    
    admin_text += f"\n**Total:** {len(ADMIN_IDS)} admins"
    admin_text += f"\n**Owner:** `{OWNER_ID}`"
    admin_text += f"\n**Your ID:** `{user_id}`"
    admin_text += f"\n**Your Status:** {'✅ Admin' if await is_admin(user_id) else '❌ Not Admin'}"
    
    await event.reply(admin_text)

@client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_handler(event):
    """Broadcast message to all groups"""
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply("❌ Sirf admin log broadcast use kar sakte hain!")
        return
    
    try:
        broadcast_msg = event.message.text.replace('/broadcast', '', 1).strip()
        if not broadcast_msg:
            await event.reply("⚠️ Message likhein!\nExample: `/broadcast Hello everyone!`")
            return
        
        msg = await event.reply("📢 Sab groups mein broadcast kar raha hoon...")
        
        dialogs = await client.get_dialogs()
        groups = [dialog for dialog in dialogs if dialog.is_group]
        
        success = 0
        failed = 0
        
        for group in groups:
            try:
                await client.send_message(group.id, f"📢 **Broadcast Message**\n\n{broadcast_msg}")
                success += 1
                await asyncio.sleep(1)
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
        await event.reply("⚠️ Yeh command sirf groups mein kaam karti hai!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply("❌ Sirf admin log mentions rok sakte hain!")
        return
    
    set_stop(event.chat_id, True)
    await event.reply("⏸️ Mentions is group mein band kar diye gaye. /resume se chalu karein.")

@client.on(events.NewMessage(pattern='/resume'))
async def resume_handler(event):
    """Resume mentions in this group"""
    if not event.is_group:
        await event.reply("⚠️ Yeh command sirf groups mein kaam karti hai!")
        return
    
    user_id = event.sender_id
    if not await is_admin(user_id):
        await event.reply("❌ Sirf admin log mentions chalu kar sakte hain!")
        return
    
    set_stop(event.chat_id, False)
    await event.reply("▶️ Mentions is group mein chalu kar diye gaye!")

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
        chat_title = event.chat.title if hasattr(event.chat, 'title') else "Unknown"
        print(f"📢 Group message in: {chat_title} (ID: {event.chat_id})")
    elif event.is_private:
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
