from telethon import TelegramClient, events, Button
from telethon.tl.types import UserStatusOnline
from telethon.utils import get_display_name
import asyncio
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import random
import re
from datetime import datetime
import json

# Import languages
from languages import LANGUAGES, LANGUAGE_LIST, TOP_LANGUAGES

# ==============================================
# CONFIGURATION
# ==============================================
api_id = int(os.environ.get('API_ID', 28761567))
api_hash = os.environ.get('API_HASH', 'b6320c0cc62a97d3a7d4e3055e6b9e0d')
bot_token = os.environ.get('BOT_TOKEN', '7798323410:AAEr5G-_15rq1H1QTTz7sWjSpEaLzN_7tuU')

OWNER_ID = 28761567  # <-- APNI ID YAHAN DALEIN
ADMIN_IDS = [OWNER_ID]
user_languages = {}

# Files
ADMIN_FILE = "admins.txt"
STOP_FILE = "stop.txt"
LANG_FILE = "languages.json"

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
                stopped = f.read().split(',')
                return str(chat_id) in stopped
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

def load_user_languages():
    global user_languages
    try:
        if os.path.exists(LANG_FILE):
            with open(LANG_FILE, 'r') as f:
                user_languages = json.load(f)
    except:
        user_languages = {}

def save_user_languages():
    try:
        with open(LANG_FILE, 'w') as f:
            json.dump(user_languages, f)
    except:
        pass

def get_user_lang(user_id):
    return user_languages.get(str(user_id), 'en')

# Load data
load_admins()
load_user_languages()

# ==============================================
# HTTP SERVER
# ==============================================

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = f'''
        <html><body>
            <h1>🤖 Mention Bot Running!</h1>
            <p>Admins: {len(ADMIN_IDS)}</p>
            <p>Owner: {OWNER_ID}</p>
            <p>Status: ✅ Online</p>
        </body></html>
        '''
        self.wfile.write(html.encode())
    
    def log_message(self, *args):
        pass

def run_http():
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
    print("📡 HTTP server running")
    server.serve_forever()

threading.Thread(target=run_http, daemon=True).start()

# ==============================================
# TELEGRAM BOT
# ==============================================

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
print("🚀 Bot started!")

# ==============================================
# COMMAND HANDLERS - FIXED ORDER
# ==============================================

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Start command"""
    user_id = event.sender_id
    is_admin = user_id in ADMIN_IDS
    lang = get_user_lang(user_id)
    
    msg = f"""
🌟 **Welcome to Mention Bot!** 🌟

👋 Hello {event.sender.first_name}!

**Your Info:**
• ID: `{user_id}`
• Status: {'👑 ADMIN' if is_admin else '👤 USER'}
• Owner: `{OWNER_ID}`

**Commands:**
• /help - Show all commands
• @all - Mention everyone
• /online - Mention online users
• /admins - Mention admins
• /random 5 - Random mentions
    """
    await event.reply(msg)

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Help command"""
    user_id = event.sender_id
    is_admin = user_id in ADMIN_IDS
    
    text = "📚 **ALL COMMANDS**\n\n"
    text += "👤 **USER:**\n"
    text += "• /start - Start bot\n"
    text += "• /help - This menu\n\n"
    
    text += "📢 **MENTION:**\n"
    text += "• @all - Mention everyone\n"
    text += "• @tagall - Mention everyone\n"
    text += "• /tagall - Mention everyone\n"
    text += "• /all - Mention everyone\n"
    text += "• /online - Mention online users\n"
    text += "• /admins - Mention admins\n"
    text += "• /random [n] - Random mentions\n\n"
    
    if is_admin:
        text += "👑 **ADMIN:**\n"
        text += "• /broadcast [msg] - Broadcast\n"
        text += "• /stop - Stop mentions\n"
        text += "• /resume - Resume mentions\n"
        text += "• /stats - Bot stats\n"
        text += "• /pause - Pause mentions\n"
    
    await event.reply(text)

# ==============================================
# MENTION COMMANDS - INDIVIDUAL HANDLERS
# ==============================================

@client.on(events.NewMessage(pattern='(?i)@all|@tagall|/tagall|/all'))
async def tagall_command(event):
    """Handle @all, @tagall, /tagall, /all"""
    if not event.is_group:
        await event.reply("❌ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⏸️ Mentions are stopped. Use /resume")
        return
    
    try:
        msg = await event.reply("🔄 Fetching members...")
        members = await client.get_participants(event.chat_id)
        
        mentions = ""
        count = 0
        total = 0
        bot = await client.get_me()
        
        for user in members:
            if not user.bot and not user.deleted and user.id != bot.id:
                emoji = random.choice(["🔥", "⭐", "💫", "✨", "🌟"])
                mention = f"[{emoji}](tg://user?id={user.id})"
                
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
        await event.reply(f"✅ {total} members mentioned!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/online'))
async def online_command(event):
    """Handle /online command"""
    if not event.is_group:
        await event.reply("❌ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⏸️ Mentions are stopped. Use /resume")
        return
    
    try:
        msg = await event.reply("🔄 Finding online members...")
        members = await client.get_participants(event.chat_id)
        
        online = []
        for user in members:
            if not user.bot and not user.deleted:
                if hasattr(user, 'status') and isinstance(user.status, UserStatusOnline):
                    online.append(user)
        
        if not online:
            await event.reply("😴 No online members found!")
            await msg.delete()
            return
        
        mentions = ""
        count = 0
        total = 0
        bot = await client.get_me()
        
        for user in online:
            if user.id != bot.id:
                mention = f"[🟢](tg://user?id={user.id})"
                
                if count < 50:
                    mentions += mention + " "
                    count += 1
                    total += 1
                else:
                    await event.reply(f"🟢 **Online:**\n\n{mentions}")
                    mentions = mention + " "
                    count = 1
                    total += 1
                    await asyncio.sleep(2)
        
        if mentions:
            await event.reply(f"🟢 **Online:**\n\n{mentions}")
        
        await msg.delete()
        await event.reply(f"✅ {total} online members mentioned!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/admins'))
async def admins_command(event):
    """Handle /admins command"""
    if not event.is_group:
        await event.reply("❌ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    try:
        msg = await event.reply("🔄 Finding admins...")
        members = await client.get_participants(event.chat_id)
        chat = await event.get_chat()
        
        admins = []
        for user in members:
            if not user.bot and not user.deleted:
                if hasattr(user, 'admin_rights') and user.admin_rights:
                    admins.append(user)
                elif hasattr(chat, 'creator_id') and user.id == chat.creator_id:
                    admins.append(user)
        
        if not admins:
            await event.reply("No admins found!")
            await msg.delete()
            return
        
        mentions = ""
        count = 0
        total = 0
        bot = await client.get_me()
        
        for user in admins:
            if user.id != bot.id:
                mention = f"[👑](tg://user?id={user.id})"
                
                if count < 50:
                    mentions += mention + " "
                    count += 1
                    total += 1
                else:
                    await event.reply(f"👑 **Admins:**\n\n{mentions}")
                    mentions = mention + " "
                    count = 1
                    total += 1
                    await asyncio.sleep(2)
        
        if mentions:
            await event.reply(f"👑 **Admins:**\n\n{mentions}")
        
        await msg.delete()
        await event.reply(f"✅ {total} admins mentioned!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/random'))
async def random_command(event):
    """Handle /random command"""
    if not event.is_group:
        await event.reply("❌ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⏸️ Mentions are stopped. Use /resume")
        return
    
    try:
        parts = event.message.text.split()
        count = 5
        if len(parts) > 1:
            try:
                count = int(parts[1])
                if count < 1:
                    count = 1
                if count > 50:
                    count = 50
            except:
                count = 5
        
        msg = await event.reply(f"🔄 Selecting {count} random members...")
        members = await client.get_participants(event.chat_id)
        
        real = [u for u in members if not u.bot and not u.deleted]
        bot = await client.get_me()
        real = [u for u in real if u.id != bot.id]
        
        if len(real) < count:
            count = len(real)
        
        if count == 0:
            await event.reply("No members to mention!")
            await msg.delete()
            return
        
        selected = random.sample(real, count)
        
        mentions = ""
        for user in selected:
            emoji = random.choice(["🎲", "🎯", "🎪", "🎨", "🎭"])
            mentions += f"[{emoji}](tg://user?id={user.id}) "
        
        await msg.delete()
        await event.reply(f"🎲 **{count} Random:**\n\n{mentions}")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ==============================================
# ADMIN COMMANDS
# ==============================================

@client.on(events.NewMessage(pattern='/stop'))
async def stop_command(event):
    """Stop mentions"""
    if not event.is_group:
        await event.reply("❌ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    set_stop(event.chat_id, True)
    await event.reply("⏸️ **Mentions stopped!** Use /resume")

@client.on(events.NewMessage(pattern='/resume'))
async def resume_command(event):
    """Resume mentions"""
    if not event.is_group:
        await event.reply("❌ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    set_stop(event.chat_id, False)
    await event.reply("▶️ **Mentions resumed!**")

@client.on(events.NewMessage(pattern='/pause'))
async def pause_command(event):
    """Pause mentions (same as stop)"""
    if not event.is_group:
        await event.reply("❌ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    set_stop(event.chat_id, True)
    await event.reply("⏸️ **Mentions paused!** Use /resume")

@client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_command(event):
    """Broadcast to all groups"""
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    parts = event.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply("⚠️ Usage: `/broadcast [message]`")
        return
    
    msg_text = parts[1].strip()
    if not msg_text:
        await event.reply("⚠️ Message cannot be empty!")
        return
    
    progress = await event.reply("📢 Broadcasting...")
    
    try:
        dialogs = await client.get_dialogs()
        groups = [d for d in dialogs if d.is_group or d.is_channel]
        
        if not groups:
            await progress.edit("❌ No groups found!")
            return
        
        success = 0
        failed = 0
        
        for i, group in enumerate(groups, 1):
            try:
                await client.send_message(group.id, f"📢 **Broadcast**\n\n{msg_text}")
                success += 1
                
                if i % 5 == 0:
                    await progress.edit(f"📢 Progress: {i}/{len(groups)} | ✅ {success} | ❌ {failed}")
                
                await asyncio.sleep(1)
            except:
                failed += 1
        
        await progress.edit(f"✅ **Broadcast Complete!**\n\nTotal: {len(groups)}\n✅ Success: {success}\n❌ Failed: {failed}")
        
    except Exception as e:
        await progress.edit(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/stats'))
async def stats_command(event):
    """Bot statistics"""
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    try:
        dialogs = await client.get_dialogs()
        groups = [d for d in dialogs if d.is_group]
        users = [d for d in dialogs if d.is_user and not d.entity.bot]
        
        text = f"""
📊 **Bot Statistics**

**Groups:** {len(groups)}
**Users:** {len(users)}
**Admins:** {len(ADMIN_IDS)}
**Owner:** `{OWNER_ID}`
**Languages:** {len(LANGUAGES)}+
"""
        await event.reply(text)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ==============================================
# LANGUAGE COMMAND
# ==============================================

@client.on(events.NewMessage(pattern='/lang'))
async def lang_command(event):
    """Change language"""
    user_id = event.sender_id
    parts = event.message.text.split()
    
    if len(parts) < 2:
        # Show available languages
        text = "🌐 **Available Languages:**\n\n"
        for code, flag, name in TOP_LANGUAGES[:10]:
            text += f"• `{code}` - {flag} {name}\n"
        text += "\nUsage: `/lang [code]`\nExample: `/lang hi` for Hindi"
        await event.reply(text)
        return
    
    lang_code = parts[1].lower()
    if lang_code in LANGUAGES:
        user_languages[str(user_id)] = lang_code
        save_user_languages()
        await event.reply(f"✅ Language changed to {LANGUAGES[lang_code]['flag']} {LANGUAGES[lang_code]['name']}!")
    else:
        await event.reply("❌ Invalid language code!")

# ==============================================
# BUTTON HANDLER
# ==============================================

@client.on(events.CallbackQuery)
async def callback_handler(event):
    """Handle button clicks"""
    data = event.data.decode()
    user_id = event.sender_id
    
    if data == 'back':
        await event.edit("🔙 Back to main menu")
    elif data == 'close':
        await event.delete()

# ==============================================
# START BOT
# ==============================================

print("\n" + "="*40)
print("🚀 MENTION BOT STARTED")
print("="*40)
print(f"👑 Owner: {OWNER_ID}")
print(f"👥 Admins: {ADMIN_IDS}")
print(f"🌐 Languages: {len(LANGUAGES)}+")
print("\n📋 Commands Ready:")
print("  • @all, @tagall, /tagall, /all")
print("  • /online, /admins, /random")
print("  • /broadcast, /stop, /resume")
print("  • /pause, /stats, /lang")
print("="*40 + "\n")

try:
    client.run_until_disconnected()
except KeyboardInterrupt:
    print("\n👋 Bot stopped")
except Exception as e:
    print(f"❌ Error: {e}")
