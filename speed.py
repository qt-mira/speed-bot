import os
import logging
import random
import asyncio
import json
from datetime import datetime, date, time, timedelta

import pytz
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Commands dictionary
COMMANDS = [
    BotCommand("start", "🎉 Start the bot"),
    BotCommand("gay", "🏳️‍🌈 Gay selector"),
    BotCommand("couple", "💞 Couple matcher"),
    BotCommand("simp", "😅 Simp detector"),
    BotCommand("toxic", "☠️ Toxic finder"),
    BotCommand("cringe", "😬 Cringe meter"),
    BotCommand("respect", "🫡 Respect giver"),
    BotCommand("sus", "👀 Sus detector"),
    BotCommand("ghost", "👻 Ghost mode"),
    BotCommand("ping", "⚡ Check response time"),
]

# Message dictionaries

START_MESSAGES = [
    "🎉 <b>Hello {user}!</b>\n\nWelcome to the fun bot! Here are the available commands:\n\n<b>🎮 Available Commands:</b>\n├─ 🌈 /gay • Random gay selection\n├─ 😅 /simp • Find today's simp\n├─ 💞 /couple • Match a couple\n├─ 💀 /toxic • Toxic person selector\n├─ 😬 /cringe • Cringe detector\n├─ 🫡 /respect • Show respect\n├─ 👀 /sus • Sus detector\n└─ 👻 /ghost • Ghost mode (night only)\n\n<b>📝 Rules:</b>\n• Each command can be used once per day per person\n• Have fun and keep it friendly!\n• Ghost command only works 6 PM - 6 AM BD time\n\nEnjoy using the bot! 🚀"
]

GAY_MESSAGES = [
    "🏳️‍🌈 {user} has been selected as today's gay person! 🌈",
    "💅 {user} is showing some fabulous energy today! ✨",
    "🌈 {user} got picked for the rainbow squad! 🏳️‍🌈",
    "⚡️ {user} is radiating some colorful vibes today! 🌈",
    "💀 {user} has been chosen for the gay category! 🏳️‍🌈",
    "👀 {user} is today's selected gay person! 🌈"
]

COUPLE_MESSAGES = [
    "💑 Today's couple is {user1} & {user2}! How cute! 💕",
    "❤️ Look at these lovebirds {user1} and {user2}! So sweet! 💖",
    "💘 {user1} and {user2} make a lovely couple today! 💝",
    "💕 Aww, {user1} and {user2} are today's chosen couple! 💞",
    "💍 {user1} and {user2} are paired up as today's couple! 💒",
    "😍 {user1} and {user2} have been matched as today's couple! 💗"
]

SIMP_MESSAGES = [
    "💸 {user} has been selected as today's simp! 💕",
    "👑 {user} is today's biggest simp! 😅",
    "📱 {user} got picked for the simp category today! 💖",
    "😩 {user} is showing some simp energy today! 💘",
    "😭 {user} has been chosen as today's simp! 💝",
    "🤡 {user} is today's selected simp! 💞"
]

TOXIC_MESSAGES = [
    "☠️ {user} is today's most toxic person! 😈",
    "🧪 {user} has been selected for the toxic category! ⚠️",
    "💀 {user} is bringing the toxic energy today! 🔥",
    "😡 {user} got picked as the toxic one today! ⚡",
    "🔥 {user} is today's toxic person! 💢",
    "🚨 {user} has been chosen for toxic behavior! ⚠️"
]

CRINGE_MESSAGES = [
    "😬 {user} is today's most cringe person! 🤪",
    "🤢 {user} has been selected for the cringe category! 😵",
    "💀 {user} is bringing maximum cringe today! 🤮",
    "📉 {user} got picked as today's cringe person! 😬",
    "🎤 {user} is showing some cringe energy! 🤐",
    "🤮 {user} has been chosen as today's cringe master! 😖"
]

RESPECT_MESSAGES = [
    "🫡 {user} deserves respect today! Much honor! 👑",
    "🙏 {user} has earned today's respect! Well done! 💯",
    "👑 {user} is today's most respectable person! 🎖️",
    "🔥 {user} gets all the respect today! Amazing! ⭐",
    "🎖️ {user} has been chosen for respect! Great job! 🏆",
    "💫 {user} deserves recognition and respect today! 🌟"
]

SUS_MESSAGES = [
    "📮 {user} is acting pretty sus today! 🤔",
    "🤔 {user} is today's most suspicious person! 👀",
    "👀 {user} got picked for being sus! Interesting... 🕵️",
    "🧍 {user} is showing some suspicious behavior! 🤨",
    "📸 {user} has been selected as today's sus person! 🔍",
    "🔍 {user} is today's most sus individual! 🤫"
]

GHOST_MESSAGES = [
    "👻 {user} has been ghosting everyone lately! 🌙",
    "🌙 {user} is today's biggest ghost! Where are you? 💀",
    "💀 {user} disappeared like a ghost! 👻",
    "🕵️‍♂️ {user} is playing ghost mode today! 🌫️",
    "📉 {user} has been selected as today's ghost! 👻",
    "📴 {user} went full ghost mode! Come back! 🌙"
]

ERROR_MESSAGES = [
    "This command only works in groups! Add me to a group to use it. 😊",
    "Not enough members in this chat to use this command! 😅",
    "Couldn't select anyone right now. Try again later! 😅",
    "This command only works in groups! Add me to a group to find couples! 💕",
    "Need at least 2 members to create a couple! 💕",
    "Couldn't find 2 people for a couple! Try again later! 😅",
    "This command only works in groups! Add me to a group to use ghost mode! 👻",
    "Not enough members for ghost mode! 👻",
    "Couldn't select a ghost today! Try again later! 👻"
]

COOLDOWN_MESSAGES = [
    "⏳ Please wait an hour before using /{command} again!",
    "⏳ You already used /{command} today! Try again tomorrow.",
    "⏰ Please wait an hour before using ghost mode again! 👻",
    "👻 Ghost mode already used today! Come back tomorrow! 🌙"
]

GHOST_TIME_MESSAGES = [
    "🌙 Ghost mode is only available from 6 PM to 6 AM BD time!\n\n⏰ Come back in {hours}h {minutes}m for spooky time! 👻"
]

BROADCAST_MESSAGES = [
    "📣 <b>Broadcast mode enabled!</b>\n\nSend me any message and I will forward it to all users.",
    "📊 <b>Broadcast sent!</b>\n\nNote: Database was removed, so actual broadcasting is disabled.\nBroadcast mode is still active. Send /start to disable.",
    "⛔ This command is restricted."
]

PING_MESSAGES = [
    "⚡ Pong! {response_time}ms"
]

HEALTH_MESSAGES = [
    "Bot is running!"
]

LOG_MESSAGES = [
    "Unauthorized broadcast attempt by user {user_id}",
    "Broadcast mode enabled for owner {user_id}",
    "Broadcasting message from owner {user_id}",
    "Bot username set: @{username}",
    "Failed to get bot info: {error}",
    "Bot commands registered successfully!",
    "Could not get chat members: {error}",
    "Broadcast mode disabled for {user_id}",
    "Health server listening on port {port}",
    "Bot starting..."
]

# Configuration

BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")
OWNER_ID = 5290407067
UPDATES_CHANNEL = "https://t.me/WorkGlows"
SUPPORT_GROUP = "https://t.me/TheCryptoElders"
BOT_USERNAME = None
BANGLADESH_TZ = 'Asia/Dhaka'

# Global variables

broadcast_mode = set()
broadcast_target = {}
daily_selections = {}
user_cooldowns = {}

# Command messages mapping
COMMAND_MESSAGES = {
    'gay': GAY_MESSAGES,
    'couple': COUPLE_MESSAGES,
    'simp': SIMP_MESSAGES,
    'toxic': TOXIC_MESSAGES,
    'cringe': CRINGE_MESSAGES,
    'respect': RESPECT_MESSAGES,
    'sus': SUS_MESSAGES,
    'ghost': GHOST_MESSAGES
}

# Utility functions

def build_name(first_name, last_name):
    """Build user display name"""
    if first_name:
        return f"{first_name}{f' {last_name}' if last_name else ''}"
    return "User"

def get_user_mention_html(user):
    """Generate HTML mention for user"""
    display = build_name(user.first_name, getattr(user, 'last_name', None))
    return f'<a href="tg://user?id={user.id}">{sanitize_html(display)}</a>'

def sanitize_html(text):
    """Sanitize HTML text"""
    import html
    return html.escape(text)

def is_night_time_in_bangladesh():
    """Check if it's night time in Bangladesh"""
    bd_tz = pytz.timezone(BANGLADESH_TZ)
    bd_time = datetime.now(bd_tz).time()
    night_start = time(18, 0)  # 6 PM
    night_end = time(6, 0)     # 6 AM
    return bd_time >= night_start or bd_time <= night_end

def get_time_until_night():
    """Get time until night in Bangladesh"""
    bd_tz = pytz.timezone(BANGLADESH_TZ)
    bd_now = datetime.now(bd_tz)
    bd_time = bd_now.time()
    if bd_time < time(18, 0):
        next_night = bd_now.replace(hour=18, minute=0, second=0, microsecond=0)
    else:
        next_night = bd_now.replace(hour=18, minute=0, second=0, microsecond=0) + timedelta(days=1)
    time_diff = next_night - bd_now
    hours = int(time_diff.total_seconds() // 3600)
    minutes = int((time_diff.total_seconds() % 3600) // 60)
    return hours, minutes

def can_use_command(user_id, chat_id, command):
    """Check if user can use command (simple cooldown system)"""
    key = f"{user_id}_{chat_id}_{command}"
    today = date.today().isoformat()
    
    if key in user_cooldowns:
        last_used_date, last_used_time = user_cooldowns[key]
        
        # Check if already used today
        if last_used_date == today:
            # Check hourly limit (1 hour cooldown)
            time_diff = datetime.now() - last_used_time
            if time_diff.total_seconds() < 3600:  # 1 hour
                return False, 'hourly_limit'
            return False, 'daily_limit'
    
    return True, 'allowed'

def mark_command_used(user_id, chat_id, command):
    """Mark command as used for cooldown tracking"""
    key = f"{user_id}_{chat_id}_{command}"
    today = date.today().isoformat()
    now = datetime.now()
    user_cooldowns[key] = (today, now)

def get_daily_selection(chat_id, command):
    """Get today's daily command selection"""
    key = f"{chat_id}_{command}_{date.today().isoformat()}"
    return daily_selections.get(key)

def save_daily_selection(chat_id, command, user_id, user_id_2=None):
    """Save daily command selection"""
    key = f"{chat_id}_{command}_{date.today().isoformat()}"
    selection = {'user_id': user_id}
    if user_id_2:
        selection['user_id_2'] = user_id_2
    daily_selections[key] = selection

def select_random_users(users, count=1, exclude=None):
    """Select random users from a list"""
    if exclude is None:
        exclude = []
    available_users = [user for user in users if user.id not in exclude]
    if len(available_users) < count:
        return available_users
    return random.sample(available_users, count)

def select_random_users_seeded(users, count=1, seed=None, exclude=None):
    """Select random users with a seed for consistent daily selection"""
    if exclude is None:
        exclude = []
    available_users = [user for user in users if user.id not in exclude]
    if len(available_users) < count:
        return available_users
    if seed:
        random.seed(seed)
    selected = random.sample(available_users, count)
    random.seed()
    return selected

# Chat member functions

async def get_chat_members(update, context):
    """Get list of chat members"""
    chat_id = update.effective_chat.id
    members = []
    
    try:
        # Get chat administrators first
        administrators = await context.bot.get_chat_administrators(chat_id)
        for admin in administrators:
            if not admin.user.is_bot:
                members.append(admin.user)
        
        # If we have enough members from admins, return them
        if len(members) >= 2:
            return members
        
        # For smaller groups, we'll work with what we have
        return members
        
    except Exception as e:
        logger.warning(LOG_MESSAGES[6].format(error=e))
        return []

# Handler functions

async def typing_action(update, context):
    """Show typing action"""
    if update.effective_chat:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

async def start_command(update, context):
    """Handle /start command"""
    user = update.effective_user
    if not user:
        return

    await typing_action(update, context)

    # Disable broadcast mode if active
    if user.id in broadcast_mode:
        broadcast_mode.discard(user.id)
        if user.id in broadcast_target:
            del broadcast_target[user.id]
        logger.info(LOG_MESSAGES[7].format(user_id=user.id))

    start_message = START_MESSAGES[0].format(user=get_user_mention_html(user))

    keyboard = [
        [
            InlineKeyboardButton("Updates", url=UPDATES_CHANNEL),
            InlineKeyboardButton("Support", url=SUPPORT_GROUP)
        ],
        [
            InlineKeyboardButton("Add Me To Your Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true" if BOT_USERNAME else "https://t.me/your_bot_username?startgroup=true")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        start_message,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )

async def handle_single_user_command(update, context, command):
    """Handle single user selection commands"""
    if not update.effective_user or not update.effective_chat:
        return

    # Only work in groups
    if update.effective_chat.type == 'private':
        await update.message.reply_text(ERROR_MESSAGES[0])
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    await typing_action(update, context)

    # Check cooldown
    can_use, reason = can_use_command(user_id, chat_id, command)
    if not can_use:
        if reason == 'hourly_limit':
            await update.message.reply_text(COOLDOWN_MESSAGES[0].format(command=command))
        else:
            await update.message.reply_text(COOLDOWN_MESSAGES[1].format(command=command))
        return

    # Check if we already have today's selection
    existing_selection = get_daily_selection(chat_id, command)
    if existing_selection:
        try:
            selected_user = await context.bot.get_chat_member(chat_id, existing_selection['user_id'])
            selected_user_mention = get_user_mention_html(selected_user.user)
            message_template = random.choice(COMMAND_MESSAGES[command])
            final_message = message_template.format(user=selected_user_mention)
            await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
            mark_command_used(user_id, chat_id, command)
            return
        except:
            pass

    # Get chat members
    members = await get_chat_members(update, context)
    
    if len(members) < 1:
        await update.message.reply_text(ERROR_MESSAGES[1])
        return

    # Select random user with seed for consistency
    seed = f"{chat_id}_{command}_{date.today().isoformat()}"
    selected_users = select_random_users_seeded(members, 1, seed)

    if not selected_users:
        await update.message.reply_text(ERROR_MESSAGES[2])
        return

    selected_user = selected_users[0]
    save_daily_selection(chat_id, command, selected_user.id)

    selected_user_mention = get_user_mention_html(selected_user)
    message_template = random.choice(COMMAND_MESSAGES[command])
    final_message = message_template.format(user=selected_user_mention)

    await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
    mark_command_used(user_id, chat_id, command)

async def handle_couple_command(update, context):
    """Handle couple command logic"""
    if not update.effective_user or not update.effective_chat:
        return
    
    # Only work in groups
    if update.effective_chat.type == 'private':
        await update.message.reply_text(ERROR_MESSAGES[3])
        return
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    command = 'couple'
    
    await typing_action(update, context)
    
    # Check cooldown
    can_use, reason = can_use_command(user_id, chat_id, command)
    if not can_use:
        if reason == 'hourly_limit':
            await update.message.reply_text(COOLDOWN_MESSAGES[0].format(command=command))
        else:
            await update.message.reply_text(COOLDOWN_MESSAGES[1].format(command=command))
        return
    
    # Check if we already have today's selection
    existing_selection = get_daily_selection(chat_id, command)
    if existing_selection:
        try:
            user1 = await context.bot.get_chat_member(chat_id, existing_selection['user_id'])
            user2 = await context.bot.get_chat_member(chat_id, existing_selection['user_id_2'])
            
            user1_mention = get_user_mention_html(user1.user)
            user2_mention = get_user_mention_html(user2.user)
            
            message_template = random.choice(COMMAND_MESSAGES[command])
            final_message = message_template.format(user1=user1_mention, user2=user2_mention)
            
            await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
            mark_command_used(user_id, chat_id, command)
            return
        except:
            pass
    
    # Get chat members
    members = await get_chat_members(update, context)
    
    if len(members) < 2:
        await update.message.reply_text(ERROR_MESSAGES[4])
        return
    
    # Select 2 random users using seeded selection for consistency
    seed = f"{chat_id}_{command}_{date.today().isoformat()}"
    selected_users = select_random_users_seeded(members, 2, seed)
    
    if len(selected_users) < 2:
        await update.message.reply_text(ERROR_MESSAGES[5])
        return
    
    user1, user2 = selected_users
    save_daily_selection(chat_id, command, user1.id, user2.id)
    
    user1_mention = get_user_mention_html(user1)
    user2_mention = get_user_mention_html(user2)
    
    message_template = random.choice(COMMAND_MESSAGES[command])
    final_message = message_template.format(user1=user1_mention, user2=user2_mention)
    
    await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
    mark_command_used(user_id, chat_id, command)

async def ghost_command(update, context):
    """Handle /ghost command (night time only)"""
    if not update.effective_user or not update.effective_chat:
        return
    
    # Only work in groups
    if update.effective_chat.type == 'private':
        await update.message.reply_text(ERROR_MESSAGES[6])
        return
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    command = 'ghost'
    
    await typing_action(update, context)
    
    # Check if it's night time in Bangladesh
    if not is_night_time_in_bangladesh():
        hours, minutes = get_time_until_night()
        await update.message.reply_text(GHOST_TIME_MESSAGES[0].format(hours=hours, minutes=minutes))
        return
    
    # Check cooldown
    can_use, reason = can_use_command(user_id, chat_id, command)
    if not can_use:
        if reason == 'hourly_limit':
            await update.message.reply_text(COOLDOWN_MESSAGES[2])
        else:
            await update.message.reply_text(COOLDOWN_MESSAGES[3])
        return
    
    # Check if we already have today's selection
    existing_selection = get_daily_selection(chat_id, command)
    if existing_selection:
        try:
            selected_user = await context.bot.get_chat_member(chat_id, existing_selection['user_id'])
            selected_user_mention = get_user_mention_html(selected_user.user)
            message_template = random.choice(COMMAND_MESSAGES[command])
            final_message = message_template.format(user=selected_user_mention)
            await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
            mark_command_used(user_id, chat_id, command)
            return
        except:
            pass
    
    # Get chat members
    members = await get_chat_members(update, context)
    
    if len(members) < 1:
        await update.message.reply_text(ERROR_MESSAGES[7])
        return
    
    # Select random user using seeded selection for consistency
    seed = f"{chat_id}_{command}_{date.today().isoformat()}"
    selected_users = select_random_users_seeded(members, 1, seed)
    
    if not selected_users:
        await update.message.reply_text(ERROR_MESSAGES[8])
        return
    
    selected_user = selected_users[0]
    save_daily_selection(chat_id, command, selected_user.id)
    
    selected_user_mention = get_user_mention_html(selected_user)
    message_template = random.choice(COMMAND_MESSAGES[command])
    final_message = message_template.format(user=selected_user_mention)
    
    await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
    mark_command_used(user_id, chat_id, command)

# Command handlers

async def gay_command(update, context):
    """Handle /gay command"""
    await handle_single_user_command(update, context, 'gay')

async def couple_command(update, context):
    """Handle /couple command"""
    await handle_couple_command(update, context)

async def simp_command(update, context):
    """Handle /simp command"""
    await handle_single_user_command(update, context, 'simp')

async def toxic_command(update, context):
    """Handle /toxic command"""
    await handle_single_user_command(update, context, 'toxic')

async def cringe_command(update, context):
    """Handle /cringe command"""
    await handle_single_user_command(update, context, 'cringe')

async def respect_command(update, context):
    """Handle /respect command"""
    await handle_single_user_command(update, context, 'respect')

async def sus_command(update, context):
    """Handle /sus command"""
    await handle_single_user_command(update, context, 'sus')

async def broadcast_command(update, context):
    """Handle /broadcast command (owner only)"""
    if not update.message.from_user or update.message.from_user.id != OWNER_ID:
        logger.warning(LOG_MESSAGES[0].format(user_id=update.message.from_user.id if update.message.from_user else 'Unknown'))
        await typing_action(update, context)
        await update.message.reply_text(BROADCAST_MESSAGES[2])
        return

    await typing_action(update, context)
    await update.message.reply_text(BROADCAST_MESSAGES[0], parse_mode=ParseMode.HTML)
    
    broadcast_mode.add(update.message.from_user.id)
    logger.info(LOG_MESSAGES[1].format(user_id=update.message.from_user.id))

async def ping_command(update, context):
    """Handle /ping command"""
    import time
    start_time = time.time()
    await typing_action(update, context)
    end_time = time.time()
    response_time = round((end_time - start_time) * 1000, 2)
    await update.message.reply_text(
        PING_MESSAGES[0].format(response_time=response_time),
        parse_mode=ParseMode.HTML
    )

async def handle_broadcast_message(update, context):
    """Handle broadcast message sending"""
    if not update.message.from_user or update.message.from_user.id not in broadcast_mode:
        return
    
    if update.message.chat.type != "private":
        return
    
    logger.info(LOG_MESSAGES[2].format(user_id=update.message.from_user.id))
    
    # For now, just acknowledge the broadcast (since we removed database)
    await update.message.reply_text(BROADCAST_MESSAGES[1], parse_mode=ParseMode.HTML)

async def on_startup(application):
    """Initialize bot on startup"""
    global BOT_USERNAME
    
    # Get bot info to set username dynamically
    try:
        bot_info = await application.bot.get_me()
        BOT_USERNAME = bot_info.username
        logger.info(LOG_MESSAGES[3].format(username=BOT_USERNAME))
    except Exception as e:
        logger.error(LOG_MESSAGES[4].format(error=e))
        BOT_USERNAME = "your_bot_username"
    
    await application.bot.set_my_commands(COMMANDS)
    logger.info(LOG_MESSAGES[5])

# HTTP server for health checks

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(HEALTH_MESSAGES[0].encode())

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(LOG_MESSAGES[8].format(port=port))
    server.serve_forever()

# Main function

def main():
    """Main function to start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("gay", gay_command))
    application.add_handler(CommandHandler("couple", couple_command))
    application.add_handler(CommandHandler("simp", simp_command))
    application.add_handler(CommandHandler("toxic", toxic_command))
    application.add_handler(CommandHandler("cringe", cringe_command))
    application.add_handler(CommandHandler("respect", respect_command))
    application.add_handler(CommandHandler("sus", sus_command))
    application.add_handler(CommandHandler("ghost", ghost_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("ping", ping_command))
    
    # Handle broadcast messages in private chat
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & ~filters.COMMAND,
        handle_broadcast_message
    ))
    
    # Register startup hook
    application.post_init = on_startup
    
    # Start the bot
    logger.info(LOG_MESSAGES[9])
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    # Start HTTP server for health checks
    threading.Thread(target=start_health_server, daemon=True).start()
    main()