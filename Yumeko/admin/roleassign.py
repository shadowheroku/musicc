import json
import os
import logging
from typing import Dict, List, Optional
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from Yumeko import app as pgram
from config import config
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save

OWNER_ID = config.OWNER_ID
sudoers_file = "sudoers.json"
logger = logging.getLogger(__name__)

# Initialize logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Helper Functions ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_roles() -> Dict[str, List[int]]:
    """Load roles from JSON file with error handling"""
    try:
        if not os.path.exists(sudoers_file):
            with open(sudoers_file, "w") as f:
                default_roles = {"Hokages": [], "Jonins": [], "Chunins": [], "Genins": []}
                json.dump(default_roles, f, indent=4)
            return default_roles
            
        with open(sudoers_file, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading roles: {e}")
        return {"Hokages": [], "Jonins": [], "Chunins": [], "Genins": []}

def save_roles(data: Dict) -> None:
    """Save roles to JSON file with error handling"""
    try:
        with open(sudoers_file, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving roles: {e}")

def ensure_owner_is_hokage() -> None:
    """Ensure OWNER_ID is always in Hokages"""
    roles = load_roles()
    if OWNER_ID not in roles["Hokages"]:
        roles["Hokages"].append(OWNER_ID)
        save_roles(roles)

async def get_user_info(client: Client, user_id: int) -> str:
    """Get user mention with fallback"""
    try:
        user = await client.get_users(user_id)
        return f"{user.mention} (`{user_id}`)"
    except Exception as e:
        logger.warning(f"Couldn't fetch user {user_id}: {e}")
        return f"Unknown User (`{user_id}`)"

def get_hierarchy_level(user_id: int) -> int:
    """Get numerical hierarchy level (0=Owner, 1=Hokage, 2=Jonin, etc)"""
    roles = load_roles()
    if user_id == OWNER_ID:
        return 0
    if user_id in roles["Hokages"]:
        return 1
    if user_id in roles["Jonins"]:
        return 2
    if user_id in roles["Chunins"]:
        return 3
    if user_id in roles["Genins"]:
        return 4
    return 999

def get_allowed_roles(assigner_id: int) -> List[str]:
    """Get roles that a user is allowed to assign"""
    assigner_level = get_hierarchy_level(assigner_id)
    
    if assigner_level == 0:  # Owner
        return ["Hokage", "Jonin", "Chunin", "Genin"]
    if assigner_level == 1:  # Hokage
        return ["Jonin", "Chunin", "Genin"]
    if assigner_level == 2:  # Jonin
        return ["Chunin", "Genin"]
    if assigner_level == 3:  # Chunin
        return ["Genin"]
    return []

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pgram.on_message(filters.command("assign", prefixes=config.COMMAND_PREFIXES))
@error
@save
async def assign_role(client: Client, message: Message):
    """Assign roles with proper hierarchy enforcement"""
    ensure_owner_is_hokage()
    sender = message.from_user
    
    # Permission check
    if get_hierarchy_level(sender.id) > 3:
        await message.reply("❌ You don't have permission to use this command.")
        return

    # Target user resolution
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
            target = await client.get_users(target_id)
        except (ValueError, IndexError):
            await message.reply("❌ Invalid user ID format.")
            return
        except Exception as e:
            logger.error(f"User lookup error: {e}")
            await message.reply("❌ Couldn't find that user.")
            return
    else:
        await message.reply("🔍 Please reply to a user or provide a valid UserID.")
        return

    # Hierarchy validation
    target_level = get_hierarchy_level(target.id)
    sender_level = get_hierarchy_level(sender.id)
    
    if target_level <= sender_level:
        await message.reply("⛔ You can only assign roles to users below your hierarchy level.")
        return

    allowed_roles = get_allowed_roles(sender.id)
    if not allowed_roles:
        await message.reply("❌ You don't have permission to assign any roles.")
        return

    # Create interactive buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=f"🛡️ {role}", 
            callback_data=f"assign:{role}:{target.id}:{sender.id}"
        )] for role in allowed_roles
    ])

    target_info = await get_user_info(client, target.id)
    await message.reply(
        f"🌟 **Assigning Role to** {target_info}\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Choose a role to assign:",
        reply_markup=buttons
    )

@pgram.on_callback_query(filters.regex(r"^assign:(.+?):(\d+):(\d+)$"))
@error
@save
async def handle_assign_callback(client: Client, callback: CallbackQuery):
    """Handle role assignment callback"""
    ensure_owner_is_hokage()
    role, target_id, sender_id = callback.data.split(":")[1:]
    target_id = int(target_id)
    sender_id = int(sender_id)

    # Validation
    if callback.from_user.id != sender_id:
        await callback.answer("🚫 Action not permitted!", show_alert=True)
        return

    roles = load_roles()
    allowed_roles = get_allowed_roles(sender_id)
    
    if role not in allowed_roles:
        await callback.answer("❌ Permission denied for this role!", show_alert=True)
        return

    # Remove existing roles
    for existing_role in ["Hokages", "Jonins", "Chunins", "Genins"]:
        if target_id in roles[existing_role]:
            roles[existing_role].remove(target_id)

    # Add new role
    role_key = f"{role}s" if role != "Genin" else "Genins"
    roles[role_key].append(target_id)
    save_roles(roles)

    # Format response
    target_info = await get_user_info(client, target_id)
    await callback.edit_message_text(
        f"✅ **Successfully Assigned**\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"• User: {target_info}\n"
        f"• Role: {role}\n"
        f"• Assigned by: {callback.from_user.mention}"
    )

@pgram.on_message(filters.command("unassign", prefixes=config.COMMAND_PREFIXES))
@error
@save
async def remove_role(client: Client, message: Message):
    """Remove roles with hierarchy enforcement"""
    ensure_owner_is_hokage()
    sender = message.from_user

    # Permission check
    if get_hierarchy_level(sender.id) > 3:
        await message.reply("❌ You don't have permission to use this command.")
        return

    # Target user resolution
    try:
        if message.reply_to_message:
            target = message.reply_to_message.from_user
        else:
            target_id = int(message.command[1])
            target = await client.get_users(target_id)
    except Exception as e:
        logger.error(f"Unassign error: {e}")
        await message.reply("❌ Invalid user or user ID.")
        return

    # Hierarchy validation
    target_level = get_hierarchy_level(target.id)
    sender_level = get_hierarchy_level(sender.id)
    
    if target_level <= sender_level:
        await message.reply("⛔ You can only unassign users below your hierarchy level.")
        return

    # Remove roles
    roles = load_roles()
    removed = False
    allowed_to_remove = get_allowed_roles(sender.id) + ["Genin"]
    
    for role in allowed_to_remove:
        role_key = f"{role}s" if role != "Genin" else "Genins"
        if target.id in roles.get(role_key, []):
            roles[role_key].remove(target.id)
            removed = True

    if removed:
        save_roles(roles)
        target_info = await get_user_info(client, target.id)
        await message.reply(
            f"🗑️ **Removed Roles**\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"• User: {target_info}\n"
            f"• Removed by: {sender.mention}"
        )
    else:
        await message.reply("ℹ️ User had no removable roles.")

@pgram.on_message(filters.command("staffs", prefixes=config.COMMAND_PREFIXES) & filters.user(OWNER_ID))
@error
@save
async def list_staffs(client: Client, message: Message):
    """Display detailed staff list with hierarchy"""
    roles = load_roles()
    response = "🔷 **Staff Hierarchy** 🔷\n\n"
    
    role_display = {
        "Hokages": "🏯 Hokages (Top Level)",
        "Jonins": "🗡️ Jonins (Senior Staff)",
        "Chunins": "⚔️ Chunins (Junior Staff)",
        "Genins": "📘 Genins (Trainees)"
    }

    for role_key, role_name in role_display.items():
        members = roles.get(role_key, [])
        response += f"**{role_name}**\n"
        
        if not members:
            response += "└ *No members*\n\n"
            continue
            
        for i, user_id in enumerate(members, 1):
            user_info = await get_user_info(client, user_id)
            prefix = "└" if i == len(members) else "├"
            response += f"{prefix} {user_info}\n"
        
        response += "\n"

    await message.reply(response)

# Initialization check
ensure_owner_is_hokage()
logger.info("Role assignment system initialized successfully")
