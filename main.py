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

# ==============================================
# FUNCTIONS DEFINITIONS - PEHLE DEFINE KARO
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
    return user_languages.get(str(user_id), 'en_in')  # Default English India

def get_text(user_id, key, **kwargs):
    """Get text in user's language"""
    lang_code = get_user_lang(user_id)
    lang_dict = LANGUAGES.get(lang_code, LANGUAGES['en_in'])
    text = lang_dict.get(key, LANGUAGES['en_in'].get(key, key))
    return text.format(**kwargs)

# ==============================================
# LOAD SAVED DATA - AB CALL KARO
# ==============================================
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
                <p>Languages: {len(LANGUAGES)}+</p>
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
        [Button.inline(get_text(user_id, 'support_btn'), b'support'),
         Button.inline(get_text(user_id, 'add_btn'), b'add_group'),
         Button.inline(get_text(user_id, 'settings_btn'), b'settings')],
        [Button.inline(get_text(user_id, 'language_btn'), b'language'),
         Button.inline(get_text(user_id, 'close_btn'), b'close')]
    ]
    return buttons

def get_settings_buttons(user_id):
    """Get settings menu buttons"""
    buttons = [
        [Button.inline(get_text(user_id, 'mention_settings'), b'settings_mention'),
         Button.inline(get_text(user_id, 'admin_settings'), b'settings_admin')],
        [Button.inline(get_text(user_id, 'group_settings'), b'settings_group'),
         Button.inline(get_text(user_id, 'language_settings'), b'language')],
        [Button.inline(get_text(user_id, 'back_btn'), b'main_menu')]
    ]
    return buttons

def get_language_buttons(user_id):
    """Get language selection buttons - 2 per row"""
    buttons = []
    
    # Top Telegram countries
    top_countries = [
        ('hi', '🇮🇳', 'हिंदी'),
        ('en_in', '🇮🇳', 'English'),
        ('id', '🇮🇩', 'Indonesia'),
        ('ru', '🇷🇺', 'Русский'),
        ('ar_eg', '🇪🇬', 'العربية'),
        ('pt_br', '🇧🇷', 'Português'),
    ]
    
    row = []
    for lang_code, flag, name in top_countries:
        button_text = f"{flag} {name}"
        row.append(Button.inline(button_text, f'lang_{lang_code}'.encode()))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    # More languages button
    buttons.append([Button.inline("🌐 More Languages", b'lang_more')])
    buttons.append([Button.inline(get_text(user_id, 'back_btn'), b'main_menu')])
    
    return buttons

# ==============================================
# BOT COMMANDS
# ==============================================

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Welcome message with buttons"""
    user_id = event.sender_id
    is_admin_user = user_id in ADMIN_IDS
    
    status = get_text(user_id, 'admin_status') if is_admin_user else get_text(user_id, 'user_status')
    
    welcome_msg = (
        f"{get_text(user_id, 'welcome_title')}\n\n"
        f"👋 Hello {event.sender.first_name}!\n\n"
        f"{get_text(user_id, 'your_info')}\n"
        f"{get_text(user_id, 'user_id', user_id=user_id)}\n"
        f"{get_text(user_id, 'status', status=status)}\n"
        f"{get_text(user_id, 'owner', owner_id=OWNER_ID)}"
    )
    
    buttons = get_main_menu_buttons(user_id)
    await event.reply(welcome_msg, buttons=buttons)

@client.on(events.CallbackQuery)
async def callback_handler(event):
    """Handle button clicks"""
    user_id = event.sender_id
    data = event.data.decode()
    
    if data == 'support':
        # Support group link
        await event.answer("Opening support group...")
        await event.edit(
            "📞 **Support Group**\n\n"
            "Join our support group for help:\n"
            "https://t.me/your_support_group",
            buttons=[[Button.inline(get_text(user_id, 'back_btn'), b'main_menu')]]
        )
    
    elif data == 'add_group':
        # Add to group
        await event.answer("Add me to your group!")
        bot_username = (await client.get_me()).username
        await event.edit(
            f"➕ **Add Me to Your Group**\n\n"
            f"1. Open this link:\n"
            f"https://t.me/{bot_username}?startgroup=start\n\n"
            f"2. Select your group\n"
            f"3. Make me admin for full features",
            buttons=[[Button.inline(get_text(user_id, 'back_btn'), b'main_menu')]]
        )
    
    elif data == 'settings':
        # Settings menu
        await event.edit(
            get_text(user_id, 'settings_title'),
            buttons=get_settings_buttons(user_id)
        )
    
    elif data == 'language':
        # Language menu
        await event.edit(
            get_text(user_id, 'language_title'),
            buttons=get_language_buttons(user_id)
        )
    
    elif data == 'lang_more':
        # More languages
        all_langs = [
            ('ms', '🇲🇾', 'Malaysia'),
            ('ar_sa', '🇸🇦', 'Saudi Arabia'),
            ('ar_ae', '🇦🇪', 'UAE'),
            ('uk', '🇺🇦', 'Ukraine'),
            ('kk', '🇰🇿', 'Kazakhstan'),
            ('de', '🇩🇪', 'Germany'),
            ('fr', '🇫🇷', 'France'),
            ('it', '🇮🇹', 'Italy'),
            ('es', '🇪🇸', 'Spain'),
            ('nl', '🇳🇱', 'Netherlands'),
            ('pl', '🇵🇱', 'Poland'),
            ('en_ng', '🇳🇬', 'Nigeria'),
        ]
        
        buttons = []
        row = []
        for lang_code, flag, name in all_langs:
            button_text = f"{flag} {name}"
            row.append(Button.inline(button_text, f'lang_{lang_code}'.encode()))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        
        buttons.append([Button.inline(get_text(user_id, 'back_btn'), b'language')])
        await event.edit("🌐 **More Languages**", buttons=buttons)
    
    elif data == 'main_menu':
        # Back to main menu
        status = '👑 ADMIN' if user_id in ADMIN_IDS else '👤 USER'
        await event.edit(
            f"{get_text(user_id, 'welcome_title')}\n\n"
            f"👋 Hello!\n\n"
            f"{get_text(user_id, 'your_info')}\n"
            f"{get_text(user_id, 'user_id', user_id=user_id)}\n"
            f"{get_text(user_id, 'status', status=status)}",
            buttons=get_main_menu_buttons(user_id)
        )
    
    elif data == 'close':
        # Close/delete message
        await event.delete()
    
    elif data.startswith('lang_'):
        # Change language
        lang_code = data.replace('lang_', '')
        user_languages[str(user_id)] = lang_code
        save_user_languages()
        
        await event.answer(f"Language changed!")
        
        # Refresh menu in new language
        status = '👑 ADMIN' if user_id in ADMIN_IDS else '👤 USER'
        await event.edit(
            f"{get_text(user_id, 'welcome_title')}\n\n"
            f"👋 Hello {event.sender.first_name}!\n\n"
            f"{get_text(user_id, 'your_info')}\n"
            f"{get_text(user_id, 'user_id', user_id=user_id)}\n"
            f"{get_text(user_id, 'status', status=status)}",
            buttons=get_main_menu_buttons(user_id)
        )
    
    elif data == 'settings_mention':
        # Mention settings
        await event.edit(
            get_text(user_id, 'mention_settings_title'),
            buttons=[[Button.inline(get_text(user_id, 'back_btn'), b'settings')]]
        )
    
    elif data == 'settings_admin':
        # Admin settings
        admin_count = len(ADMIN_IDS)
        await event.edit(
            f"{get_text(user_id, 'admin_settings_title')}\n\n"
            f"{get_text(user_id, 'total_admins', count=admin_count)}",
            buttons=[[Button.inline(get_text(user_id, 'back_btn'), b'settings')]]
        )

# ==============================================
# MENTION COMMANDS
# ==============================================

@client.on(events.NewMessage)
async def mention_handler(event):
    """Handle @all, @tagall, /tagall, /all"""
    
    if not event.is_group:
        return
    
    text = event.message.text.strip().lower()
    
    if text not in ['@all', '@tagall', '/tagall', '/all']:
        return
    
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply(get_text(user_id, 'admin_only'))
        return
    
    if is_stopped(event.chat_id):
        await event.reply(get_text(user_id, 'stopped'))
        return
    
    try:
        msg = await event.reply("🔄 Fetching members...")
        members = await client.get_participants(event.chat_id)
        
        # Send mentions
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

@client.on(events.NewMessage(pattern='/hello'))
async def hello_handler(event):
    """Mention with custom message"""
    if not event.is_group:
        await event.reply(get_text(event.sender_id, 'group_only'))
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply(get_text(user_id, 'admin_only'))
        return
    
    if is_stopped(event.chat_id):
        await event.reply(get_text(user_id, 'stopped'))
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
        await event.reply(f"✅ {total} members mentioned!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ==============================================
# ADMIN MANAGEMENT
# ==============================================

@client.on(events.NewMessage(pattern='/promote'))
async def promote_handler(event):
    """Promote user to admin"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply(get_text(user_id, 'admin_only'))
        return
    
    # Get target user from reply or input
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
            await event.reply(get_text(user_id, 'user_not_found'))
            return
    
    if target_id in ADMIN_IDS:
        await event.reply(get_text(user_id, 'already_admin'))
        return
    
    ADMIN_IDS.append(target_id)
    save_admins()
    
    await event.reply(
        f"{get_text(user_id, 'promoted')}\n\n"
        f"User ID: `{target_id}`\n"
        f"Total Admins: {len(ADMIN_IDS)}"
    )

@client.on(events.NewMessage(pattern='/demote'))
async def demote_handler(event):
    """Demote user from admin"""
    user_id = event.sender_id
    
    if user_id not in ADMIN_IDS:
        await event.reply(get_text(user_id, 'admin_only'))
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
            await event.reply(get_text(user_id, 'user_not_found'))
            return
    
    if target_id == OWNER_ID:
        await event.reply("❌ Cannot demote owner!")
        return
    
    if target_id not in ADMIN_IDS:
        await event.reply(get_text(user_id, 'not_admin'))
        return
    
    ADMIN_IDS.remove(target_id)
    save_admins()
    
    await event.reply(
        f"{get_text(user_id, 'demoted')}\n\n"
        f"User ID: `{target_id}`\n"
        f"Total Admins: {len(ADMIN_IDS)}"
    )

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
        await event.reply(get_text(user_id, 'admin_only'))
        return
    
    parts = event.message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await event.reply(get_text(user_id, 'broadcast_usage'))
        return
    
    broadcast_msg = parts[1].strip()
    
    if not broadcast_msg:
        await event.reply(get_text(user_id, 'broadcast_usage'))
        return
    
    progress = await event.reply(get_text(user_id, 'broadcast_start'))
    
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
                        f"{get_text(user_id, 'broadcast_start')}\n\n"
                        f"Progress: {i}/{len(groups)}\n"
                        f"Success: {success}\n"
                        f"Failed: {failed}"
                    )
                
                await asyncio.sleep(1.2)
                
            except:
                failed += 1
        
        await progress.edit(
            f"{get_text(user_id, 'broadcast_done')}\n\n"
            f"Total Groups: {len(groups)}\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}"
        )
        
    except Exception as e:
        await progress.edit(f"❌ Error: {str(e)}")

# ==============================================
# OTHER COMMANDS
# ==============================================

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Help command"""
    user_id = event.sender_id
    await event.reply(get_text(user_id, 'help_text'))

@client.on(events.NewMessage(pattern='/stats'))
async def stats_handler(event):
    """Bot statistics"""
    user_id = event.sender_id
    
    try:
        dialogs = await client.get_dialogs()
        groups = [d for d in dialogs if d.is_group]
        users = [d for d in dialogs if d.is_user and not d.entity.bot]
        
        stats_text = (
            f"{get_text(user_id, 'stats_title')}\n\n"
            f"{get_text(user_id, 'total_groups', count=len(groups))}\n"
            f"{get_text(user_id, 'total_users', count=len(users))}\n"
            f"{get_text(user_id, 'total_admins_stat', count=len(ADMIN_IDS))}\n"
            f"{get_text(user_id, 'bot_version')}"
        )
        
        await event.reply(stats_text)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern='/ping'))
async def ping_handler(event):
    """Check bot status"""
    start = datetime.now()
    msg = await event.reply("🏓 **Pinging...**")
    end = datetime.now()
    ms = (end - start).microseconds / 1000
    await msg.edit(f"🏓 **Pong!**\n**Response time:** `{ms}ms`")

@client.on(events.NewMessage(pattern='/stop'))
async def stop_handler(event):
    """Stop mentions in group"""
    if not event.is_group:
        await event.reply(get_text(event.sender_id, 'group_only'))
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply(get_text(user_id, 'admin_only'))
        return
    
    set_stop(event.chat_id, True)
    await event.reply("⏸️ Mentions stopped in this group. Use /resume to start again.")

@client.on(events.NewMessage(pattern='/resume'))
async def resume_handler(event):
    """Resume mentions in group"""
    if not event.is_group:
        await event.reply(get_text(event.sender_id, 'group_only'))
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply(get_text(user_id, 'admin_only'))
        return
    
    set_stop(event.chat_id, False)
    await event.reply("▶️ Mentions resumed in this group!")

@client.on(events.NewMessage(pattern='/online'))
async def online_handler(event):
    """Mention online members"""
    if not event.is_group:
        await event.reply(get_text(event.sender_id, 'group_only'))
        return
    
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.reply(get_text(user_id, 'admin_only'))
        return
    
    if is_stopped(event.chat_id):
        await event.reply(get_text(user_id, 'stopped'))
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
print(f"🌐 Languages: {len(LANGUAGES)}+")
print("✅ Bot is running! Press Ctrl+C to stop.")

try:
    client.run_until_disconnected()
except KeyboardInterrupt:
    print("\n👋 Bot stopped by user")
except Exception as e:
    print(f"❌ Error: {e}")
