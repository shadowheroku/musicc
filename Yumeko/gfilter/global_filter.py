from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import config
from Yumeko import app, GFILTER_GROUP
from Yumeko.database import gfilter_collection
import time

OWNER_ID = config.OWNER_ID

# Set Global Filter
@app.on_message(filters.command("setgfilter") & filters.user(OWNER_ID))
async def set_global_filter(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.sticker:
        await message.reply("**Reply to a sticker to set as global filter!**")
        return

    if len(message.command) < 3:
        await message.reply("**Usage:**\n/setgfilter [filter_name] [channel_id]")
        return

    filter_name = " ".join(message.command[1:-1]).lower()  # Allow multiple words
    channel_id = message.command[-1]

    try:
        channel = await client.get_chat(channel_id)
    except Exception as e:
        await message.reply(f"**Channel Error:**\n`{e}`")
        return

    try:
        me = await client.get_chat_member(channel.id, (await client.get_me()).id)
        if me.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            await message.reply("**I'm not admin in that channel!**")
            return
    except Exception as e:
        await message.reply(f"**Admin Check Error:**\n`{e}`")
        return

    sticker_id = message.reply_to_message.sticker.file_id

    await gfilter_collection.update_one(
        {"_id": filter_name},
        {"$set": {
            "channel_id": channel.id,
            "channel_name": channel.title,
            "sticker_id": sticker_id,
            "timestamp": time.time()
        }},
        upsert=True
    )

    await message.reply(f"**✅ Global Filter Set!**\n**Name:** `{filter_name}`\n**Channel:** {channel.title}")

# Global Filter Trigger
@app.on_message(filters.group & filters.text & ~filters.command(["start", "help", "setgfilter", "removegfilter", "gfilters"]), group=GFILTER_GROUP)  
async def global_filter_handler(client: Client, message: Message):
    filter_name = message.text.strip().lower()
    filter_data = await gfilter_collection.find_one({"_id": filter_name})
    
    if not filter_data:
        return

    try:
        invite_link = await client.create_chat_invite_link(
            chat_id=filter_data["channel_id"],
            name=f"GFilter_{filter_name}",
            expire_date=datetime.now() + timedelta(minutes=40)
        )
    except Exception as e:
        await message.reply("**Error generating invite link!**")
        return

    await message.reply_sticker(
        sticker=filter_data["sticker_id"],
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text=filter_data["channel_name"],
                url=invite_link.invite_link
            )
        ]])
    )

# List Global Filters
@app.on_message(filters.command("gfilters") & filters.user(OWNER_ID))
async def list_global_filters(client: Client, message: Message):
    filters_list = []
    
    async for filter_data in gfilter_collection.find({}):  # Fetch all global filters
        filter_name = filter_data.get("_id", "Unknown")
        channel_name = filter_data.get("channel_name", "Unknown Channel")
        channel_id = filter_data.get("channel_id", "Unknown ID")

        filters_list.append(f"• `{filter_name}` - {channel_name} (`{channel_id}`)")

    if not filters_list:
        await message.reply("**No global filters set!**")
        return

    filters_text = f"**📝 Global Filters ({len(filters_list)}):**\n\n" + "\n".join(filters_list)

    # Handle Telegram's 4096-character message limit
    if len(filters_text) > 4000:
        with open("gfilters.txt", "w") as f:
            f.write(filters_text)
        await message.reply_document("gfilters.txt", caption="📜 **List of Global Filters**")
    else:
        await message.reply(filters_text)



# Remove Global Filter
@app.on_message(filters.command("removegfilter") & filters.user(OWNER_ID))
async def remove_global_filter(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("**Usage:**\n/removegfilter [filter_name]")
        return

    filter_name = " ".join(message.command[1:]).lower()  # Allow multiple words
    result = await gfilter_collection.delete_one({"_id": filter_name})

    if result.deleted_count:
        await message.reply(f"**✅ Removed global filter:** `{filter_name}`")
    else:
        await message.reply("**❌ No such global filter found!**")

