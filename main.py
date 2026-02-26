from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import asyncio

# API Details (Apni values yaha dalein)
api_id = 29568441  # Apna api_id dalein
api_hash = 'b32ec0fb66d22da6f77d355fbace4f2a'
bot_token = '8574288227:AAGT1pauRQSnUiTbxVPPFVJl5SGS-Olh968'

# Bot Client
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

@bot.on(events.NewMessage(pattern='/tagall'))
async def tagall(event):
    # Sirf groups me kaam karega
    if event.is_group:
        msg = await event.reply("🔄 Saare members ko mention kar raha hoon...")
        
        # Group ke saare members nikalna
        members = await bot.get_participants(event.chat_id)
        
        # Mentions list banana
        mentions = ""
        count = 0
        for user in members:
            if not user.bot and not user.deleted:  # Sirf real users ko tag karega
                mention = f"[{user.first_name}](tg://user?id={user.id})"
                
                # Ek message me 50 members tak mention karega (Telegram limit)
                if count <= 50:
                    mentions += mention + " "
                    count += 1
                else:
                    await event.reply(mentions)
                    mentions = mention + " "
                    count = 1
                    await asyncio.sleep(2)  # 2 second ka gap
        
        # Bache hue mentions bhejna
        if mentions:
            await event.reply(mentions)
        
        await msg.delete()
    else:
        await event.reply("⚠️ Ye command sirf groups me kaam karegi.")

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("👋 Main group mention bot hoon!\n/tagall se saare members ko tag kar sakte ho.")

print("🤖 Bot chal raha hai...")
bot.run_until_disconnected()
