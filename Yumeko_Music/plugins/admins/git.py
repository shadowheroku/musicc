import os
import sys
from pyrogram import filters
from Yumeko_Music import app
from config import config 


@app.on_message(filters.command("mrestart") & filters.user(config.OWNER_ID))
async def restart_command(client, message):
    try:
        restart_message = await message.reply("**ᴏɴɪɪ-ᴄʜᴀɴ ʏᴜᴍᴇᴋᴏ ɪꜱ ʙᴇɪɴɢ ʀᴇꜱᴛᴀʀᴛᴇᴅ !!**")
        os.execvp(sys.executable, [sys.executable, "-m", "Yumeko_Music"])
    except Exception as e:
        await message.reply(f"Rᴇsᴛᴀʀᴛ ғᴀɪʟᴇᴅ ᴡɪᴛʜ ᴇʀʀᴏʀ: {str(e)}")
        