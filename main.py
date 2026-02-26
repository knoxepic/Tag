from telethon import TelegramClient, events, sync
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize the client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Command handler for /all
@client.on(events.NewMessage(pattern='/all'))
async def all_handler(event):
    if event.is_group:
        all_users = []
        offset_user = 0    # keep track of batch offset
        limit_user = 200   # define the batch size

        while True:
            participants = await client(GetParticipantsRequest(
                event.chat_id, ChannelParticipantsSearch(''),
                offset_user, limit_user, hash=0
            ))
            if not participants.users:
                break
            all_users.extend([user.username or user.first_name for user in participants.users])
            offset_user += len(participants.users)

        # Splitting message if it's too long
        MESSAGE_LIMIT = 4096
        message = ''
        for user in all_users:
            if len(message) + len(user) + 1 > MESSAGE_LIMIT:
                await event.respond(message)
                message = ''
            message += f'@{user} '

        if message:
            await event.respond(message)

client.run_until_disconnected()
