import socket
import urllib3
from pyrogram import filters
from Yumeko_Music import app
from Yumeko_Music.misc import SUDOERS

from Yumeko_Music.utils.decorators.language import language
from Yumeko_Music.utils.pastebin import AviaxBin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


async def is_heroku():
    return "heroku" in socket.getfqdn()


@app.on_message(filters.command(["mgetlog", "mlogs", "mgetlogs"]) & SUDOERS)
@language
async def log_(client, message, _):
    try:
        await message.reply_document(document="log.txt")
    except:
        await message.reply_text(_["server_1"])


