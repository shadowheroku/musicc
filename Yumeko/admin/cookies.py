import os
import shutil
from pyrogram import filters
from Yumeko import app
from config import config 

# Define the cookies folder path
COOKIES_FOLDER = "cookies"

# Ensure the cookies folder exists
if not os.path.exists(COOKIES_FOLDER):
    os.makedirs(COOKIES_FOLDER)

@app.on_message(filters.command("cookies") & filters.reply & filters.user(config.OWNER_ID))
async def handle_reply_cookies(client, message):
    # Ensure the replied message contains a file
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply("Please reply to a valid text file.")
        return
    
    # Get the file from the replied message
    file = message.reply_to_message.document

    # Check if the file is a .txt file
    if not file.file_name.endswith(".txt"):
        await message.reply("The file must be a .txt file.")
        return

    # Clear the cookies folder
    shutil.rmtree(COOKIES_FOLDER)
    os.makedirs(COOKIES_FOLDER)

    # Download the file
    file_path = await client.download_media(file, file_name=os.path.join(COOKIES_FOLDER, file.file_name))
    await message.reply(f"Cookies updated! File saved as: `{file_path}`")

@app.on_message(filters.command("cookies") & ~filters.reply & filters.user(config.OWNER_ID))
async def handle_text_cookies(client, message):
    # Parse the command argument
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Please provide the content for the text file.")
        return

    # Get the content for the text file
    content = args[1]

    # Clear the cookies folder
    shutil.rmtree(COOKIES_FOLDER)
    os.makedirs(COOKIES_FOLDER)

    # Create a new text file with the given content
    file_path = os.path.join(COOKIES_FOLDER, "cookies.txt")
    with open(file_path, "w") as f:
        f.write(content)

    await message.reply(f"Cookies updated! File created at: `{file_path}`")

