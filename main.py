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

# ==============================================
# CONFIGURATION
# ==============================================
api_id = int(os.environ.get('API_ID', 28761567))
api_hash = os.environ.get('API_HASH', 'b6320c0cc62a97d3a7d4e3055e6b9e0d')
bot_token = os.environ.get('BOT_TOKEN', '7798323410:AAEr5G-_15rq1H1QTTz7sWjSpEaLzN_7tuU')

OWNER_ID = 7957361876  # <-- APNI ID YAHAN DALEIN
ADMIN_IDS = [OWNER_ID]
user_languages = {}

# Files
ADMIN_FILE = "admins.txt"
STOP_FILE = "stop.txt"
LANG_FILE = "languages.json"

# ==============================================
# LANGUAGES (Simplified for now)
# ==============================================

LANGUAGES = {
    'en': {
        'name': 'English',
        'flag': '🇬🇧',
        'welcome': "🌟 Welcome to Mention Bot! 🌟",
    },
    'hi': {
        'name': 'हिंदी',
        'flag': '🇮🇳',
        'welcome': "🌟 मेंशन बॉट में आपका स्वागत है! 🌟",
    }
}

TOP_LANGUAGES = [
    ('en', '🇬🇧', 'English'),
    ('hi', '🇮🇳', 'हिंदी'),
]

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
        <html>
            <head><title>Mention Bot</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>🤖 Mention Bot is Running!</h1>
                <p>Admins: {len(ADMIN_IDS)}</p>
                <p>Owner: {OWNER_ID}</p>
                <p>Status: ✅ Online</p>
            </body>
        </html>
        '''
        self.wfile.write(html.encode())
    
    def log_message(self, *args):
        pass

def run_http():
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
    print("📡 HTTP server running on port 10000")
    server.serve_forever()

threading.Thread(target=run_http, daemon=True).start()

# ==============================================
# TELEGRAM BOT
# ==============================================

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
print("🚀 Bot started!")

# ==============================================
# BUTTON FUNCTIONS
# ==============================================

def get_main_menu_buttons():
    """Main menu buttons - 3 per row"""
    buttons = [
        [Button.inline("📞 Support", b'support'),
         Button.inline("➕ Add to Group", b'add_group'),
         Button.inline("⚙️ Settings", b'settings')],
        [Button.inline("🌐 Language", b'language'),
         Button.inline("📋 Commands", b'commands'),
         Button.inline("❌ Close", b'close')]
    ]
    return buttons

def get_settings_buttons():
    """Settings menu buttons"""
    buttons = [
        [Button.inline("📢 Mention Settings", b'settings_mention'),
         Button.inline("👑 Admin Settings", b'settings_admin')],
        [Button.inline("👥 Group Settings", b'settings_group'),
         Button.inline("🌐 Language", b'language')],
        [Button.inline("🔙 Back", b'main_menu')]
    ]
    return buttons

def get_language_buttons():
    """Language selection buttons"""
    buttons = []
    row = []
    for lang_code, flag, name in TOP_LANGUAGES:
        row.append(Button.inline(f"{flag} {name}", f'lang_{lang_code}'.encode()))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([Button.inline("🔙 Back", b'main_menu')])
    return buttons

def get_commands_buttons(is_admin):
    """Commands menu buttons"""
    buttons = [
        [Button.inline("👤 User Commands", b'cmds_user'),
         Button.inline("📢 Mention Commands", b'cmds_mention')]
    ]
    if is_admin:
        buttons.append([Button.inline("👑 Admin Commands", b'cmds_admin')])
    buttons.append([Button.inline("🔙 Back", b'main_menu')])
    return buttons

# ==============================================
# COMMAND HANDLERS
# ==============================================

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Start command with buttons"""
    user_id = event.sender_id
    is_admin = user_id in ADMIN_IDS
    
    msg = f"""
🌟 **Welcome to Mention Bot!** 🌟

👋 Hello {event.sender.first_name}!

**Your Information:**
• ID: `{user_id}`
• Status: {'👑 ADMIN' if is_admin else '👤 USER'}
• Owner: `{OWNER_ID}`

**📌 Quick Guide:**
• Use buttons below
• Type /help for all commands
"""
    await event.reply(msg, buttons=get_main_menu_buttons())

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Help command"""
    user_id = event.sender_id
    is_admin = user_id in ADMIN_IDS
    
    text = "📚 **ALL COMMANDS**\n\n"
    text += "👤 **USER COMMANDS:**\n"
    text += "• /start - Start the bot\n"
    text += "• /help - Show help menu\n\n"
    
    text += "📢 **MENTION COMMANDS:**\n"
    text += "• @all - Mention everyone\n"
    text += "• @tagall - Mention everyone\n"
    text += "• /tagall - Mention everyone\n"
    text += "• /all - Mention everyone\n"
    text += "• /online - Mention online users\n"
    text += "• /admins - Mention admins\n"
    text += "• /random [n] - Random mentions (1-50)\n\n"
    
    if is_admin:
        text += "👑 **ADMIN COMMANDS:**\n"
        text += "• /broadcast [msg] - Broadcast to all groups\n"
        text += "• /stop - Stop mentions in group\n"
        text += "• /resume - Resume mentions in group\n"
        text += "• /stats - Bot statistics\n"
        text += "• /pause - Pause mentions\n"
    
    await event.reply(text)

# ==============================================
# MENTION COMMANDS
# ==============================================

@client.on(events.NewMessage(pattern=r'(?i)(@all|@tagall|/tagall|/all)$'))
async def tagall_handler(event):
    """Mention everyone"""
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
async def online_handler(event):
    """Mention online users"""
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
                    await event.reply(f"🟢 **Online Members:**\n\n{mentions}")
                    mentions = mention + " "
                    count = 1
                    total += 1
                    await asyncio.sleep(2)
        
        if mentions:
            await event.reply(f"🟢 **Online Members:**\n\n{mentions}")
        
        await msg.delete()
        await event.reply(f"✅ {total} online members mentioned!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/admins'))
async def admins_handler(event):
    """Mention admins"""
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
                    await event.reply(f"👑 **Group Admins:**\n\n{mentions}")
                    mentions = mention + " "
                    count = 1
                    total += 1
                    await asyncio.sleep(2)
        
        if mentions:
            await event.reply(f"👑 **Group Admins:**\n\n{mentions}")
        
        await msg.delete()
        await event.reply(f"✅ {total} admins mentioned!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/random'))
async def random_handler(event):
    """Random mentions"""
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
        await event.reply(f"🎲 **{count} Random Members:**\n\n{mentions}")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ==============================================
# ADMIN COMMANDS
# ==============================================

@client.on(events.NewMessage(pattern='/stop'))
async def stop_handler(event):
    """Stop mentions"""
    if not event.is_group:
        await event.reply("❌ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    set_stop(event.chat_id, True)
    await event.reply("⏸️ **Mentions stopped!** Use /resume to start again.")

@client.on(events.NewMessage(pattern='/resume'))
async def resume_handler(event):
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
async def pause_handler(event):
    """Pause mentions"""
    if not event.is_group:
        await event.reply("❌ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    set_stop(event.chat_id, True)
    await event.reply("⏸️ **Mentions paused!** Use /resume to resume.")

@client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_handler(event):
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
                await client.send_message(group.id, f"📢 **Broadcast Message**\n\n{msg_text}")
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
async def stats_handler(event):
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
"""
        await event.reply(text)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ==============================================
# CALLBACK HANDLER (BUTTONS)
# ==============================================

@client.on(events.CallbackQuery)
async def callback_handler(event):
    """Handle all button clicks"""
    user_id = event.sender_id
    data = event.data.decode()
    is_admin = user_id in ADMIN_IDS
    
    if data == 'support':
        await event.answer("Opening support...")
        await event.edit(
            "📞 **Support Group**\n\n"
            "Join our support group:\n"
            "https://t.me/your_support_group",
            buttons=[[Button.inline("🔙 Back", b'main_menu')]]
        )
    
    elif data == 'add_group':
        await event.answer("Adding to group...")
        bot_username = (await client.get_me()).username
        await event.edit(
            f"➕ **Add Me to Your Group**\n\n"
            f"1. Click: https://t.me/{bot_username}?startgroup=start\n"
            f"2. Select your group\n"
            f"3. Make me admin",
            buttons=[[Button.inline("🔙 Back", b'main_menu')]]
        )
    
    elif data == 'settings':
        await event.edit(
            "⚙️ **Bot Settings**\n\nSelect a category:",
            buttons=get_settings_buttons()
        )
    
    elif data == 'language':
        await event.edit(
            "🌐 **Select Language**",
            buttons=get_language_buttons()
        )
    
    elif data == 'commands':
        await event.edit(
            "📋 **Commands Menu**",
            buttons=get_commands_buttons(is_admin)
        )
    
    elif data == 'main_menu':
        msg = f"""
🌟 **Welcome to Mention Bot!** 🌟

👋 Hello!

**Your Information:**
• ID: `{user_id}`
• Status: {'👑 ADMIN' if is_admin else '👤 USER'}
• Owner: `{OWNER_ID}`
"""
        await event.edit(msg, buttons=get_main_menu_buttons())
    
    elif data == 'close':
        await event.delete()
    
    elif data == 'cmds_user':
        text = "👤 **USER COMMANDS:**\n\n"
        text += "• /start - Start bot\n"
        text += "• /help - Show help"
        await event.edit(text, buttons=[[Button.inline("🔙 Back", b'commands')]])
    
    elif data == 'cmds_mention':
        text = "📢 **MENTION COMMANDS:**\n\n"
        text += "• @all - Mention everyone\n"
        text += "• @tagall - Mention everyone\n"
        text += "• /tagall - Mention everyone\n"
        text += "• /all - Mention everyone\n"
        text += "• /online - Mention online\n"
        text += "• /admins - Mention admins\n"
        text += "• /random [n] - Random"
        await event.edit(text, buttons=[[Button.inline("🔙 Back", b'commands')]])
    
    elif data == 'cmds_admin':
        if is_admin:
            text = "👑 **ADMIN COMMANDS:**\n\n"
            text += "• /broadcast [msg] - Broadcast\n"
            text += "• /stop - Stop mentions\n"
            text += "• /resume - Resume mentions\n"
            text += "• /stats - Statistics\n"
            text += "• /pause - Pause"
            await event.edit(text, buttons=[[Button.inline("🔙 Back", b'commands')]])
        else:
            await event.answer("Admins only!", alert=True)
    
    elif data == 'settings_mention':
        await event.edit(
            "📢 **Mention Settings**\n\n"
            "• Max: 50 per message\n"
            "• Delay: 2 seconds\n"
            "• Emojis: ✅ ON",
            buttons=[[Button.inline("🔙 Back", b'settings')]]
        )
    
    elif data == 'settings_admin':
        await event.edit(
            f"👑 **Admin Settings**\n\n"
            f"• Total Admins: {len(ADMIN_IDS)}\n"
            f"• Owner: `{OWNER_ID}`\n"
            f"• You: {'✅ Admin' if is_admin else '❌ Not Admin'}",
            buttons=[[Button.inline("🔙 Back", b'settings')]]
        )
    
    elif data == 'settings_group':
        await event.edit(
            "👥 **Group Settings**\n\n"
            "• /stop - Stop mentions\n"
            "• /resume - Resume\n"
            "• /pause - Pause",
            buttons=[[Button.inline("🔙 Back", b'settings')]]
        )
    
    elif data.startswith('lang_'):
        lang = data.replace('lang_', '')
        user_languages[str(user_id)] = lang
        save_user_languages()
        await event.answer(f"Language changed!")
        await event.edit(
            f"✅ Language changed to {LANGUAGES[lang]['flag']} {LANGUAGES[lang]['name']}",
            buttons=[[Button.inline("🔙 Back", b'main_menu')]]
        )

# ==============================================
# START BOT
# ==============================================

print("\n" + "="*50)
print("🚀 MENTION BOT STARTED - ALL COMMANDS WORKING")
print("="*50)
print(f"👑 Owner: {OWNER_ID}")
print(f"👥 Admins: {ADMIN_IDS}")
print("\n📋 Commands Ready:")
print("  • @all, @tagall, /tagall, /all")
print("  • /online, /admins, /random")
print("  • /broadcast, /stop, /resume")
print("  • /pause, /stats")
print("\n🔘 Buttons Ready:")
print("  • Support, Add to Group, Settings")
print("  • Language, Commands, Close")
print("="*50 + "\n")

try:
    client.run_until_disconnected()
except KeyboardInterrupt:
    print("\n👋 Bot stopped")
except Exception as e:
    print(f"❌ Error: {e}")
