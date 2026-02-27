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
from languages import *

# ==============================================
# CONFIGURATION
# ==============================================
api_id = int(os.environ.get('API_ID', 28761567))
api_hash = os.environ.get('API_HASH', 'b6320c0cc62a97d3a7d4e3055e6b9e0d')
bot_token = os.environ.get('BOT_TOKEN', '7798323410:AAEr5G-_15rq1H1QTTz7sWjSpEaLzN_7tuU')

OWNER_ID = 7957361876  # <-- APNI ID YAHAN DALEIN

# Admin list - initially sirf aap
ADMIN_IDS = [OWNER_ID]

# User language preferences
user_languages = {}

# File for persistent storage
ADMIN_FILE = "admins.txt"
STOP_FILE = "stop.txt"
LANG_FILE = "languages.json"
GROUPS_FILE = "groups.txt"

# ==============================================
# FUNCTIONS DEFINITIONS
# ==============================================

def load_admins():
    """Load admins from file"""
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
    """Save admins to file"""
    try:
        with open(ADMIN_FILE, 'w') as f:
            f.write(','.join(str(id) for id in ADMIN_IDS))
    except:
        pass

def is_stopped(chat_id):
    """Check if mentions are stopped in this chat"""
    try:
        if os.path.exists(STOP_FILE):
            with open(STOP_FILE, 'r') as f:
                stopped_chats = f.read().split(',')
                return str(chat_id) in stopped_chats
    except:
        pass
    return False

def set_stop(chat_id, stop=True):
    """Stop or resume mentions in a chat"""
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
    """Load user language preferences"""
    global user_languages
    try:
        if os.path.exists(LANG_FILE):
            with open(LANG_FILE, 'r') as f:
                user_languages = json.load(f)
    except:
        user_languages = {}

def save_user_languages():
    """Save user language preferences"""
    try:
        with open(LANG_FILE, 'w') as f:
            json.dump(user_languages, f)
    except:
        pass

def get_user_lang(user_id):
    """Get user's selected language"""
    return user_languages.get(str(user_id), 'en_in')

def get_text(user_id, key, **kwargs):
    """Get text in user's language"""
    lang_code = get_user_lang(user_id)
    lang_dict = LANGUAGES.get(lang_code, LANGUAGES['en_in'])
    text = lang_dict.get(key, LANGUAGES['en_in'].get(key, key))
    return text.format(**kwargs)

# Load saved data
load_admins()
load_user_languages()

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
                <p>Languages: 20+</p>
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

# ==============================================
# BUTTON FUNCTIONS
# ==============================================

def get_main_menu_buttons(user_id):
    """Get main menu buttons - 3 buttons per row"""
    buttons = [
        [Button.inline("📞 Support", b'support'),
         Button.inline("➕ Add to Group", b'add_group'),
         Button.inline("⚙️ Settings", b'settings')],
        [Button.inline("🌐 Language", b'language'),
         Button.inline("📋 Commands", b'commands'),
         Button.inline("❌ Close", b'close')]
    ]
    return buttons

def get_settings_buttons(user_id):
    """Get settings menu buttons"""
    buttons = [
        [Button.inline("📢 Mention Settings", b'settings_mention'),
         Button.inline("👑 Admin Settings", b'settings_admin')],
        [Button.inline("👥 Group Settings", b'settings_group'),
         Button.inline("🌐 Language", b'language')],
        [Button.inline("🔙 Back", b'main_menu')]
    ]
    return buttons

def get_language_buttons(user_id):
    """Get language selection buttons"""
    buttons = []
    
    # Top languages
    top_langs = [
        ('hi', '🇮🇳', 'हिंदी'),
        ('en_in', '🇮🇳', 'English'),
        ('id', '🇮🇩', 'Indonesia'),
        ('ru', '🇷🇺', 'Русский'),
        ('ar_eg', '🇪🇬', 'العربية'),
        ('pt_br', '🇧🇷', 'Português'),
        ('ms', '🇲🇾', 'Malaysia'),
        ('ar_sa', '🇸🇦', 'العربية'),
        ('de', '🇩🇪', 'Deutsch'),
        ('fr', '🇫🇷', 'Français'),
    ]
    
    row = []
    for lang_code, flag, name in top_langs:
        row.append(Button.inline(f"{flag} {name}", f'lang_{lang_code}'.encode()))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([Button.inline("🔙 Back", b'main_menu')])
    
    return buttons

def get_commands_buttons(user_id):
    """Get commands menu buttons"""
    is_admin = user_id in ADMIN_IDS
    
    buttons = [
        [Button.inline("👤 User Commands", b'cmds_user'),
         Button.inline("📢 Mention Commands", b'cmds_mention')]
    ]
    
    if is_admin:
        buttons.append([Button.inline("👑 Admin Commands", b'cmds_admin')])
    
    buttons.append([Button.inline("🔙 Back", b'main_menu')])
    
    return buttons

# ==============================================
# ALL COMMANDS LIST
# ==============================================

COMMANDS = {
    'user': [
        ('/start', 'Start the bot'),
        ('/help', 'Show help menu'),
        ('/id', 'Show your ID'),
        ('/myid', 'Show your ID'),
        ('/ping', 'Check bot status'),
    ],
    'mention': [
        ('@all', 'Mention everyone'),
        ('@tagall', 'Mention everyone'),
        ('/tagall', 'Mention everyone'),
        ('/all', 'Mention everyone'),
        ('/hello [msg]', 'Mention with message'),
        ('/online', 'Mention online users'),
        ('/admins', 'Mention admins'),
        ('/random [n]', 'Random mentions (1-50)'),
        ('/hidetag', 'Hide tag (no message)'),
    ],
    'admin': [
        ('/promote [id/@user]', 'Promote user to admin'),
        ('/demote [id/@user]', 'Demote user from admin'),
        ('/adminlist', 'List all admins'),
        ('/broadcast [msg]', 'Broadcast to all groups'),
        ('/stop', 'Stop mentions in group'),
        ('/resume', 'Resume mentions in group'),
        ('/stats', 'Bot statistics'),
        ('/groups', 'List my groups'),
        ('/owner', 'Show owner info'),
    ]
}

# ==============================================
# BOT COMMANDS
# ==============================================

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Welcome message with buttons"""
    user_id = event.sender_id
    is_admin_user = user_id in ADMIN_IDS
    
    welcome_msg = f"""
🌟 **Welcome to Mention Bot!** 🌟

👋 Hello {event.sender.first_name}!

**Your Information:**
• Your ID: `{user_id}`
• Status: {'👑 ADMIN' if is_admin_user else '👤 USER'}
• Bot Owner: `{OWNER_ID}`

**📌 Quick Guide:**
• Use buttons below for navigation
• Type /help for all commands
• Add me to group and make admin

**🌐 Languages:** 20+ Languages Supported
"""
    
    buttons = get_main_menu_buttons(user_id)
    await event.reply(welcome_msg, buttons=buttons)

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Show all commands"""
    user_id = event.sender_id
    is_admin = user_id in ADMIN_IDS
    
    help_text = "📚 **ALL COMMANDS**\n\n"
    
    help_text += "**👤 USER COMMANDS:**\n"
    for cmd, desc in COMMANDS['user']:
        help_text += f"• `{cmd}` - {desc}\n"
    
    help_text += "\n**📢 MENTION COMMANDS:**\n"
    for cmd, desc in COMMANDS['mention']:
        help_text += f"• `{cmd}` - {desc}\n"
    
    if is_admin:
        help_text += "\n**👑 ADMIN COMMANDS:**\n"
        for cmd, desc in COMMANDS['admin']:
            help_text += f"• `{cmd}` - {desc}\n"
    
    help_text += "\n**💡 Tips:**\n"
    help_text += "• Bot needs to be admin in group\n"
    help_text += "• Max 50 mentions per message\n"
    help_text += "• Use /stop to pause mentions\n"
    
    await event.reply(help_text)

@client.on(events.NewMessage(pattern='/id'))
@client.on(events.NewMessage(pattern='/myid'))
async def id_handler(event):
    """Show user ID"""
    user_id = event.sender_id
    is_admin = user_id in ADMIN_IDS
    
    await event.reply(
        f"🆔 **Your Information**\n\n"
        f"**ID:** `{user_id}`\n"
        f"**Username:** @{event.sender.username or 'N/A'}\n"
        f"**Name:** {event.sender.first_name}\n"
        f"**Admin:** {'✅ Yes' if is_admin else '❌ No'}\n"
        f"**Owner:** `{OWNER_ID}`"
    )

@client.on(events.NewMessage(pattern='/ping'))
async def ping_handler(event):
    """Check bot status"""
    start = datetime.now()
    msg = await event.reply("🏓 **Pinging...**")
    end = datetime.now()
    ms = (end - start).microseconds / 1000
    await msg.edit(f"🏓 **Pong!**\n**Response time:** `{ms}ms`")

@client.on(events.NewMessage(pattern='/owner'))
async def owner_handler(event):
    """Show owner info"""
    try:
        owner = await client.get_entity(OWNER_ID)
        name = get_display_name(owner)
        username = f"@{owner.username}" if owner.username else "No username"
        
        await event.reply(
            f"👑 **Owner Information**\n\n"
            f"**Name:** {name}\n"
            f"**Username:** {username}\n"
            f"**ID:** `{OWNER_ID}`"
        )
    except:
        await event.reply(f"👑 **Owner ID:** `{OWNER_ID}`")

@client.on(events.NewMessage(pattern='/groups'))
async def groups_handler(event):
    """List groups where bot is admin"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    msg = await event.reply("🔄 Fetching your groups...")
    
    try:
        dialogs = await client.get_dialogs()
        groups = []
        
        for dialog in dialogs:
            if dialog.is_group or dialog.is_channel:
                groups.append(dialog)
        
        if not groups:
            await msg.edit("📭 I'm not in any groups!")
            return
        
        text = f"📋 **My Groups ({len(groups)}):**\n\n"
        for i, group in enumerate(groups[:10], 1):
            text += f"{i}. {group.name} (ID: `{group.id}`)\n"
        
        if len(groups) > 10:
            text += f"\n... and {len(groups) - 10} more groups"
        
        await msg.edit(text)
        
    except Exception as e:
        await msg.edit(f"❌ Error: {str(e)}")

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
        
        stats_text = f"""
📊 **Bot Statistics**

**📁 Groups:**
• Total Groups: {len(groups)}

**👥 Users:**
• Total Users: {len(users)}
• Admins: {len(ADMIN_IDS)}

**🤖 Bot Info:**
• Owner: `{OWNER_ID}`
• Languages: 20+
• Version: 4.0
"""
        await event.reply(stats_text)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ==============================================
# CALLBACK HANDLER
# ==============================================

@client.on(events.CallbackQuery)
async def callback_handler(event):
    """Handle button clicks"""
    user_id = event.sender_id
    data = event.data.decode()
    
    if data == 'support':
        await event.answer("Opening support group...")
        await event.edit(
            "📞 **Support Group**\n\n"
            "Join our support group for help:\n"
            "https://t.me/your_support_group\n\n"
            "• Report bugs\n"
            "• Request features\n"
            "• Get help",
            buttons=[[Button.inline("🔙 Back", b'main_menu')]]
        )
    
    elif data == 'add_group':
        await event.answer("Add me to your group!")
        bot_username = (await client.get_me()).username
        await event.edit(
            f"➕ **Add Me to Your Group**\n\n"
            f"**Step 1:** Click this link:\n"
            f"https://t.me/{bot_username}?startgroup=start\n\n"
            f"**Step 2:** Select your group\n\n"
            f"**Step 3:** Make me admin for full features\n\n"
            f"✅ That's it! Now use /tagall",
            buttons=[[Button.inline("🔙 Back", b'main_menu')]]
        )
    
    elif data == 'settings':
        await event.edit(
            "⚙️ **Bot Settings**\n\n"
            "Select a setting category:",
            buttons=get_settings_buttons(user_id)
        )
    
    elif data == 'language':
        await event.edit(
            "🌐 **Select Language**\n\n"
            "Choose your preferred language:",
            buttons=get_language_buttons(user_id)
        )
    
    elif data == 'commands':
        await event.edit(
            "📋 **Commands Menu**\n\n"
            "Select command category:",
            buttons=get_commands_buttons(user_id)
        )
    
    elif data == 'cmds_user':
        text = "**👤 USER COMMANDS:**\n\n"
        for cmd, desc in COMMANDS['user']:
            text += f"• `{cmd}` - {desc}\n"
        await event.edit(text, buttons=[[Button.inline("🔙 Back", b'commands')]])
    
    elif data == 'cmds_mention':
        text = "**📢 MENTION COMMANDS:**\n\n"
        for cmd, desc in COMMANDS['mention']:
            text += f"• `{cmd}` - {desc}\n"
        await event.edit(text, buttons=[[Button.inline("🔙 Back", b'commands')]])
    
    elif data == 'cmds_admin':
        if user_id in ADMIN_IDS:
            text = "**👑 ADMIN COMMANDS:**\n\n"
            for cmd, desc in COMMANDS['admin']:
                text += f"• `{cmd}` - {desc}\n"
            await event.edit(text, buttons=[[Button.inline("🔙 Back", b'commands')]])
        else:
            await event.answer("Only admins can view this!", alert=True)
    
    elif data == 'settings_mention':
        await event.edit(
            "📢 **Mention Settings**\n\n"
            "• Max mentions per message: 50\n"
            "• Delay between messages: 2 sec\n"
            "• Emoji mentions: ✅ ON\n"
            "• Hide tag: Available\n\n"
            "Use commands:\n"
            "/tagall - Normal mention\n"
            "/hidetag - Hidden mention",
            buttons=[[Button.inline("🔙 Back", b'settings')]]
        )
    
    elif data == 'settings_admin':
        admin_count = len(ADMIN_IDS)
        await event.edit(
            f"👑 **Admin Settings**\n\n"
            f"• Total Admins: {admin_count}\n"
            f"• Owner ID: `{OWNER_ID}`\n\n"
            f"**Your Status:** {'✅ Admin' if user_id in ADMIN_IDS else '❌ Not Admin'}\n\n"
            f"Use /adminlist to see all admins",
            buttons=[[Button.inline("🔙 Back", b'settings')]]
        )
    
    elif data == 'settings_group':
        await event.edit(
            "👥 **Group Settings**\n\n"
            "• /stop - Stop mentions\n"
            "• /resume - Resume mentions\n"
            "• /groups - List my groups\n\n"
            "**Note:** Bot needs to be admin",
            buttons=[[Button.inline("🔙 Back", b'settings')]]
        )
    
    elif data == 'main_menu':
        is_admin_user = user_id in ADMIN_IDS
        welcome_msg = f"""
🌟 **Welcome to Mention Bot!** 🌟

👋 Hello!

**Your Information:**
• Your ID: `{user_id}`
• Status: {'👑 ADMIN' if is_admin_user else '👤 USER'}
• Bot Owner: `{OWNER_ID}`

**📌 Quick Guide:**
• Use buttons below for navigation
• Type /help for all commands
        """
        await event.edit(welcome_msg, buttons=get_main_menu_buttons(user_id))
    
    elif data == 'close':
        await event.delete()
    
    elif data.startswith('lang_'):
        lang_code = data.replace('lang_', '')
        user_languages[str(user_id)] = lang_code
        save_user_languages()
        
        await event.answer(f"Language changed!")
        
        # Refresh menu
        is_admin_user = user_id in ADMIN_IDS
        welcome_msg = f"""
🌟 **Welcome to Mention Bot!** 🌟

👋 Hello!

**Your Information:**
• Your ID: `{user_id}`
• Status: {'👑 ADMIN' if is_admin_user else '👤 USER'}
• Bot Owner: `{OWNER_ID}`

**📌 Quick Guide:**
• Use buttons below for navigation
• Type /help for all commands
        """
        await event.edit(welcome_msg, buttons=get_main_menu_buttons(user_id))

# ==============================================
# MENTION COMMANDS HANDLER
# ==============================================

@client.on(events.NewMessage)
async def mention_handler(event):
    """Handle all mention commands"""
    
    if not event.is_group:
        return
    
    text = event.message.text.strip().lower()
    
    # Check for mention commands
    if text in ['@all', '@tagall', '/tagall', '/all']:
        await handle_tagall(event)
    elif text.startswith('/hello'):
        await handle_hello(event)
    elif text == '/online':
        await handle_online(event)
    elif text == '/admins':
        await handle_admins(event)
    elif text.startswith('/random'):
        await handle_random(event)
    elif text == '/hidetag':
        await handle_hidetag(event)

async def handle_tagall(event):
    """Handle @all, @tagall, /tagall, /all"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⚠️ Mentions are stopped in this group. Use /resume to start again.")
        return
    
    try:
        msg = await event.reply("🔄 Fetching members...")
        members = await client.get_participants(event.chat_id)
        
        mentions = ""
        count = 0
        total = 0
        bot_me = await client.get_me()
        
        for user in members:
            if not user.bot and not user.deleted and user.id != bot_me.id:
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

async def handle_hello(event):
    """Handle /hello command"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⚠️ Mentions are stopped in this group. Use /resume to start again.")
        return
    
    try:
        custom_text = event.message.text.replace('/hello', '', 1).strip()
        if not custom_text:
            custom_text = "Hello everyone! 👋"
        
        msg = await event.reply("🔄 Preparing mentions...")
        members = await client.get_participants(event.chat_id)
        
        mentions = ""
        count = 0
        total = 0
        bot_me = await client.get_me()
        
        for user in members:
            if not user.bot and not user.deleted and user.id != bot_me.id:
                emoji = random.choice(["🔥", "⭐", "💫", "✨", "🌟"])
                mention = f"[{emoji}](tg://user?id={user.id})"
                
                if count < 50:
                    mentions += mention + " "
                    count += 1
                    total += 1
                else:
                    await event.reply(f"{custom_text}\n\n{mentions}")
                    mentions = mention + " "
                    count = 1
                    total += 1
                    await asyncio.sleep(2)
        
        if mentions:
            await event.reply(f"{custom_text}\n\n{mentions}")
        
        await msg.delete()
        await event.reply(f"✅ {total} members mentioned with: {custom_text[:50]}")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def handle_online(event):
    """Handle /online command"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
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
        
        mentions = ""
        count = 0
        total = 0
        bot_me = await client.get_me()
        
        for user in online_users:
            if user.id != bot_me.id:
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

async def handle_admins(event):
    """Handle /admins command"""
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
        bot_me = await client.get_me()
        
        for user in admins:
            if user.id != bot_me.id:
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

async def handle_random(event):
    """Handle /random command"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⚠️ Mentions are stopped in this group. Use /resume to start again.")
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
        
        real_members = [user for user in members if not user.bot and not user.deleted]
        
        if len(real_members) < count:
            count = len(real_members)
        
        random_members = random.sample(real_members, count)
        
        mentions = ""
        for user in random_members:
            emoji = random.choice(["🎲", "🎯", "🎪", "🎨", "🎭"])
            mentions += f"[{emoji}](tg://user?id={user.id}) "
        
        await msg.delete()
        await event.reply(f"🎲 **{count} Random Members:**\n\n{mentions}")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def handle_hidetag(event):
    """Handle /hidetag command"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    if is_stopped(event.chat_id):
        await event.reply("⚠️ Mentions are stopped in this group. Use /resume to start again.")
        return
    
    try:
        msg = await event.reply("🔄 Preparing hidden mentions...")
        members = await client.get_participants(event.chat_id)
        
        mentions = ""
        count = 0
        total = 0
        bot_me = await client.get_me()
        
        for user in members:
            if not user.bot and not user.deleted and user.id != bot_me.id:
                mention = f"[‎](tg://user?id={user.id})"  # Invisible character
                mentions += mention
                total += 1
        
        await event.reply(mentions)
        await msg.delete()
        await event.reply(f"✅ {total} members hidden mentioned!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ==============================================
# ADMIN MANAGEMENT COMMANDS
# ==============================================

@client.on(events.NewMessage(pattern='/promote'))
async def promote_handler(event):
    """Promote user to admin"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    # Get target user
    if event.message.reply_to_msg_id:
        reply_msg = await event.get_reply_message()
        target_id = reply_msg.sender_id
    else:
        parts = event.message.text.split()
        if len(parts) < 2:
            await event.reply("⚠️ Usage: `/promote [id/@username]` or reply to message")
            return
        
        input_text = parts[1]
        try:
            if input_text.startswith('@'):
                user = await client.get_entity(input_text)
                target_id = user.id
            else:
                target_id = int(input_text)
        except:
            await event.reply("❌ User not found!")
            return
    
    if target_id in ADMIN_IDS:
        await event.reply("⚠️ User is already an admin!")
        return
    
    ADMIN_IDS.append(target_id)
    save_admins()
    
    await event.reply(f"✅ **Admin Promoted!**\n\nUser ID: `{target_id}`\nTotal Admins: {len(ADMIN_IDS)}")

@client.on(events.NewMessage(pattern='/demote'))
async def demote_handler(event):
    """Demote user from admin"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    if event.message.reply_to_msg_id:
        reply_msg = await event.get_reply_message()
        target_id = reply_msg.sender_id
    else:
        parts = event.message.text.split()
        if len(parts) < 2:
            await event.reply("⚠️ Usage: `/demote [id/@username]` or reply to message")
            return
        
        input_text = parts[1]
        try:
            if input_text.startswith('@'):
                user = await client.get_entity(input_text)
                target_id = user.id
            else:
                target_id = int(input_text)
        except:
            await event.reply("❌ User not found!")
            return
    
    if target_id == OWNER_ID:
        await event.reply("❌ Cannot demote owner!")
        return
    
    if target_id not in ADMIN_IDS:
        await event.reply("⚠️ User is not an admin!")
        return
    
    ADMIN_IDS.remove(target_id)
    save_admins()
    
    await event.reply(f"✅ **Admin Demoted!**\n\nUser ID: `{target_id}`\nTotal Admins: {len(ADMIN_IDS)}")

@client.on(events.NewMessage(pattern='/adminlist'))
async def adminlist_handler(event):
    """List all admins"""
    user_id = event.sender_id
    
    admin_text = "👑 **Admin List:**\n\n"
    
    for admin_id in ADMIN_IDS:
        try:
            user = await client.get_entity(admin_id)
            name = user.first_name or "Unknown"
            username = f"@{user.username}" if user.username else "No username"
            admin_text += f"• {name} ({username}) - `{admin_id}`\n"
        except:
            admin_text += f"• Unknown User - `{admin_id}`\n"
    
    admin_text += f"\nTotal: {len(ADMIN_IDS)} admins"
    admin_text += f"\nOwner: `{OWNER_ID}`"
    
    await event.reply(admin_text)

# ==============================================
# BROADCAST COMMAND
# ==============================================

@client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_handler(event):
    """Broadcast message to all groups"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    parts = event.message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await event.reply("⚠️ Usage: `/broadcast [message]`")
        return
    
    broadcast_msg = parts[1].strip()
    
    if not broadcast_msg:
        await event.reply("⚠️ Message cannot be empty!")
        return
    
    progress = await event.reply("📢 **Broadcast starting...**")
    
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
                await client.send_message(
                    group.id,
                    f"📢 **Broadcast Message**\n\n{broadcast_msg}"
                )
                success += 1
                
                if i % 5 == 0:
                    await progress.edit(
                        f"📢 **Broadcasting...**\n\n"
                        f"Progress: {i}/{len(groups)}\n"
                        f"Success: {success}\n"
                        f"Failed: {failed}"
                    )
                
                await asyncio.sleep(1.2)
                
            except:
                failed += 1
        
        await progress.edit(
            f"✅ **Broadcast Complete!**\n\n"
            f"Total Groups: {len(groups)}\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}"
        )
        
    except Exception as e:
        await progress.edit(f"❌ Error: {str(e)}")

# ==============================================
# STOP/RESUME COMMANDS
# ==============================================

@client.on(events.NewMessage(pattern='/stop'))
async def stop_handler(event):
    """Stop mentions in group"""
    if not event.is_group:
        await event.reply("⚠️ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    set_stop(event.chat_id, True)
    await event.reply("⏸️ **Mentions stopped in this group!**\nUse /resume to start again.")

@client.on(events.NewMessage(pattern='/resume'))
async def resume_handler(event):
    """Resume mentions in group"""
    if not event.is_group:
        await event.reply("⚠️ This command only works in groups!")
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply("❌ Only admins can use this command!")
        return
    
    set_stop(event.chat_id, False)
    await event.reply("▶️ **Mentions resumed in this group!**")

# ==============================================
# AUTO DETECT
# ==============================================

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
print(f"🌐 Languages: 20+")
print("✅ Bot is running! Press Ctrl+C to stop.")
print("📌 All commands loaded:")
print("   • @all, @tagall, /tagall, /all")
print("   • /hello, /online, /admins, /random, /hidetag")
print("   • /promote, /demote, /adminlist, /broadcast")
print("   • /stop, /resume, /stats, /groups, /owner")

try:
    client.run_until_disconnected()
except KeyboardInterrupt:
    print("\n👋 Bot stopped by user")
except Exception as e:
    print(f"❌ Error: {e}")
