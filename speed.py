import os
import logging
import random
import asyncio
import json
import sqlite3
from datetime import datetime, date, time, timedelta
from contextlib import contextmanager

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

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")
OWNER_ID = 5290407067

# Official channels
UPDATES_CHANNEL = "https://t.me/WorkGlows"
SUPPORT_GROUP = "https://t.me/TheCryptoElders"
BOT_USERNAME = None

# Broadcast system
broadcast_mode = set()
broadcast_target = {}

# Aura points system
AURA_POINTS = {
    'gay': -100,
    'couple': 100,
    'simp': -100,
    'toxic': -100,
    'cringe': -100,
    'respect': 500,
    'sus': -100,
    'ghost': -200,
}

# Command messages for different actions
COMMAND_MESSAGES = {
    'gay': [
        "🏳️‍🌈 NAHHHH {user} just dropped the GAY BOMB mid-chat 😭🔥 Bro fruity as HELL 💀",
        "💅 Yo chat, {user} switched sides like it’s Fortnite teams 😭🌈 Real zesty activities going on 😩",
        "🌈 AYYOOO! {user} said 'he fine asl' out loud... that’s GAY as hell LMAO 😭🔥",
        "⚡️ Who let {user} equip the glitter rizz?! GAY ENERGY DETECTED 💀💀",
        "💀 Chat! {user} out here fruity walkin' like he in a pride parade everyday 😭",
        "👀 {user} got the rainbow aura maxed out... whole vibe fruity af 🏳️‍🌈💅"
    ],
    'couple': [
    "💑 UGLY ASS COUPLE ALERT 😭 {user1} & {user2} tryna act like anime lovebirds 💀 somebody break 'em up!",
    "❤️ These two clowns {user1} and {user2} just dropped a COUPLE post like anybody asked 💀 nobody care bruh 😭",
    "💘 AIN’T NO WAY {user1} called {user2} ‘pookie bear’ in public... internet over, go home 💀",
    "💕 Chat! COUPLE energy from {user1} and {user2} OD right now... got me gaggin 😩💀",
    "💍 Yo {user1}, blink twice if {user2} holdin’ you hostage with them long ass love quotes 😭🔥",
    "😩 COUPLE-ass vibes detected — {user1} out here soft-smiling at {user2} like a Hallmark movie 😭💔"
	],
    'simp': [
    "💸 SIMP OF THE YEAR goes to {user} — bruh dropped 50 bucks just to say 'good night queen' 😭😭😭 down bad as hell!",
    "👑 LMAOOOO {user} typed ‘you deserve better’ under her thirst trap... SIT YO SIMP ASS DOWN 💀 clown behavior fr",
    "📱 {user} in SIMP mode so hard he clapped when she posted her dog 💀 bruh ain't even her man 😭",
    "😩 {user} simpin at LEVEL 1000 — said ‘ily’ after she replied 'k' 💀 GET HELP 😭",
    "😭 {user} got friendzoned last week and STILL simpin... bro got no survival instinct 💔",
    "🤡 Chat! {user} watched her 8-min makeup tutorial and commented ‘u slayed queen’... ELITE SIMP ENERGY 😭💀"
	],
    'toxic': [
    "☠️ AYYOO {user} on full TOXIC timing — violated someone’s whole existence in 3 damn words 😭🔥",
    "🧪 {user} TOXIC as hell! Ratio’d a kid AND flamed the mod in the same breath 💀 menace behavior",
    "💀 Chat, {user} got that ‘don’t talk to me unless you wanna cry’ aura… full-on VILLAIN VIBES 😭",
    "😡 TOXIC MODE: ACTIVATED. {user} flamed someone’s mom and called it ‘character growth’ 💀💀",
    "🔥 {user} built like a final boss — straight TOXIC RAGE 24/7, no cooldown 😭💢",
    "🚨 {user} banned HIMSELF from the groupchat just to roast everyone from the outside 😭💀 certified hater"
	],
    'cringe': [
    "😬 Bro... {user} just posted 'good vibes only' with a mirror selfie… that CRINGE physically hurt me 💀 delete that shit",
    "🤢 {user} tried to drop RIZZ with ‘did it hurt when you fell from heaven?’… CRINGE OVERLOAD 🤮 CHAT I’M GONE 😭",
    "💀 Peak CRINGE unlocked — {user} made a TikTok dancing to a slow song lookin like a brick 😭 what was that bro",
    "📉 {user} typed ‘she my whole world’ after 2 days of texting… EL CRINGE RIZZ detected 💀",
    "🎤 Yo chat! {user} sent a voice note with that fake deep voice tryna be sexy… CRINGE IN 4K 😩",
    "🤮 {user} out here droppin fake deep quotes like ‘pain changes people’ with a tear filter… CRINGE KING 😭💀"
	],
    'respect': [
        "🫡 REAL ONE ALERT 🔥 {user} just did something no man has ever done before — I RESPECT IT 😤",
        "🙏 Bro moved SILENT but deadly... RESPECT the sigma grind {user} 💯",
        "👑 W MAN W MAN W MAN! {user} walked in and the room saluted 😤🔥",
        "🔥 RESPECT to the homie. {user} dropped a move so smooth it gave me goosebumps 😩",
        "🎖️ That wasn’t luck, that was STRATEGY. RESPECT the hustle {user} 💪",
        "💫 Chat, {user} pulled the most GIGACHAD thing ever. RESPECT where it’s due 💥"
    ],
    'sus': [
    "📮 {user} bein mad SUS today... liked his homie’s mirror selfie and commented 'cute af' 😭 NAHHHH WHAT?!",
    "🤔 Chat... {user} moaned mid-lobby and said ‘my bad’... SUS LEVEL 9000 😭💀",
    "👀 {user} got that ‘might kiss the homies goodnight’ vibe rn... BRO BE SERIOUS 💀",
    "🧍 SUS VIBES DETECTED. {user} been biting his lip in every pic like he on Demon Time 😭",
    "📸 Chat! {user} whispered 'ayo daddy' to the bot then muted... FULL SUS MODE ACTIVATED 💀💀",
    "🔍 {user} said ‘homies can cuddle too’ with a straight face… GET HIM OUTTA HERE 😭 SUS KING"
	],
    'ghost': [
        "👻 Where TF is {user}? GHOSTED us like we owed him money 😭💀",
        "🌙 Bro hit us with that Casper energy. {user} straight GHOST since last week 💀",
        "💀 {user} disappeared harder than my grades mid-semester 😭",
        "🕵️‍♂️ We tryna summon {user} like he a damn spirit. GHOST MODE 9000 💀",
        "📉 {user} aura dropped to zero. GHOSTED chat, GHOSTED life 😩",
        "📴 Nahhhh {user} went GHOST and didn't even say bye... fake friend vibes 😭💔"
    ]
}

# Timezone configuration
BANGLADESH_TZ = 'Asia/Dhaka'

# Member collection settings
COLLECT_MEMBERS_ON_JOIN = True
COLLECT_MEMBERS_ON_MESSAGE = True
MAX_MEMBERS_PER_BATCH = 200

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "speed_aura_bot.db")

# Database layer
local_data = threading.local()

@contextmanager
def get_db_connection():
    """Get database connection with proper error handling"""
    if not hasattr(local_data, 'conn'):
        local_data.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        local_data.conn.row_factory = sqlite3.Row
    
    try:
        yield local_data.conn
    except Exception as e:
        local_data.conn.rollback()
        raise e

def init_database():
    """Initialize database tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                aura_points INTEGER DEFAULT 0,
                is_bot INTEGER DEFAULT 0,
                language_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0
            );
        """)

        # Chat members table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                status TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, user_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)

        # Command usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                command TEXT,
                used_date DATE,
                last_announcement TIMESTAMP,
                UNIQUE(user_id, chat_id, command, used_date),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)

        # Daily selections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                command TEXT,
                selected_user_id INTEGER,
                selected_user_id_2 INTEGER,
                selection_date DATE,
                selection_data TEXT,
                UNIQUE(chat_id, command, selection_date)
            );
        """)

        conn.commit()
        logger.info("SPEED'S DATABASE INITIALIZED SUCCESSFULLY! W SETUP! 💯")

def add_or_update_user(user_id, username=None, first_name=None, last_name=None, is_bot=False, language_code=None):
    """Add or update user in database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT aura_points, message_count FROM users WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.execute("""
                UPDATE users SET
                    username = ?,
                    first_name = ?,
                    last_name = ?,
                    is_bot = ?,
                    language_code = ?,
                    message_count = message_count + 1,
                    last_seen = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (username, first_name, last_name, is_bot, language_code, user_id))
        else:
            cursor.execute("""
                INSERT INTO users (
                    user_id, username, first_name, last_name, is_bot, language_code,
                    aura_points, message_count, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, 0, 1, CURRENT_TIMESTAMP)
            """, (user_id, username, first_name, last_name, is_bot, language_code))
        
        conn.commit()

def add_chat_member(chat_id, user_id, status='member'):
    """Add or update chat member"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO chat_members (
                chat_id, user_id, status, last_active
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (chat_id, user_id, status))
        conn.commit()

def update_member_activity(chat_id, user_id):
    """Update member activity timestamp"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chat_members
            SET last_active = CURRENT_TIMESTAMP
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        
        if cursor.rowcount == 0:
            add_chat_member(chat_id, user_id)
        
        conn.commit()

def update_aura_points(user_id, points):
    """Update user aura points"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET aura_points = aura_points + ? WHERE user_id = ?
        """, (points, user_id))
        conn.commit()

def can_use_command(user_id, chat_id, command):
    """Check if user can use command (cooldown system)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        today = date.today().isoformat()
        cursor.execute("""
            SELECT last_announcement FROM command_usage
            WHERE user_id = ? AND chat_id = ? AND command = ? AND used_date = ?
        """, (user_id, chat_id, command, today))
        row = cursor.fetchone()
        
        if row:
            last_ann = row['last_announcement']
            if last_ann:
                last_time = datetime.fromisoformat(last_ann)
                if (datetime.now() - last_time).total_seconds() < 3600:
                    return False, 'hourly_limit'
            return False, 'daily_limit'
        return True, 'allowed'

def mark_command_used(user_id, chat_id, command):
    """Mark command as used for cooldown tracking"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        today = date.today().isoformat()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO command_usage (
                user_id, chat_id, command, used_date, last_announcement
            )
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, chat_id, command, today, now))
        conn.commit()

def get_leaderboard(chat_id, limit=10):
    """Get aura leaderboard for chat"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.username, u.first_name, u.last_name, u.aura_points
            FROM users u
            JOIN chat_members cm ON cm.user_id = u.user_id
            WHERE cm.chat_id = ? AND u.is_bot = 0
            ORDER BY u.aura_points DESC
            LIMIT ?
        """, (chat_id, limit))
        return cursor.fetchall()

def get_chat_users(chat_id):
    """Get all users in chat"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.username, u.first_name, u.last_name
            FROM users u
            JOIN chat_members cm ON cm.user_id = u.user_id
            WHERE cm.chat_id = ? 
              AND cm.status IN ('member','administrator','creator') 
              AND u.is_bot = 0
        """, (chat_id,))
        return cursor.fetchall()

def get_all_users():
    """Get all users globally"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT user_id FROM users WHERE is_bot = 0')
        return [row[0] for row in cursor.fetchall()]

def get_all_groups():
    """Get all groups bot is in"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT chat_id FROM chat_members WHERE chat_id < 0')
        return [row[0] for row in cursor.fetchall()]

def get_active_chat_members(chat_id):
    """Get active chat members (last 30 days)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute("""
            SELECT u.user_id, u.username, u.first_name, u.last_name
            FROM users u
            JOIN chat_members cm ON cm.user_id = u.user_id
            WHERE cm.chat_id = ? 
              AND cm.last_active >= ?
              AND cm.status IN ('member','administrator','creator')
              AND u.is_bot = 0
        """, (chat_id, thirty_days_ago))
        return cursor.fetchall()

def save_daily_selection(chat_id, command, user_id, user_id_2=None, selection_data=None):
    """Save daily command selection"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        today = date.today().isoformat()
        data_json = json.dumps(selection_data) if selection_data else None
        cursor.execute("""
            INSERT OR REPLACE INTO daily_selections (
                chat_id, command, selected_user_id, selected_user_id_2, selection_date, selection_data
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chat_id, command, user_id, user_id_2, today, data_json))
        conn.commit()

def get_daily_selection(chat_id, command):
    """Get today's daily command selection"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        today = date.today().isoformat()
        cursor.execute("""
            SELECT selected_user_id, selected_user_id_2, selection_data
            FROM daily_selections
            WHERE chat_id = ? AND command = ? AND selection_date = ?
        """, (chat_id, command, today))
        row = cursor.fetchone()
        
        if row:
            return {
                'user_id': row['selected_user_id'],
                'user_id_2': row['selected_user_id_2'],
                'data': json.loads(row['selection_data']) if row['selection_data'] else None
            }
        return None

def get_chat_member_count(chat_id):
    """Get count of chat members"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM chat_members
            WHERE chat_id = ? 
              AND status IN ('member','administrator','creator')
        """, (chat_id,))
        return cursor.fetchone()['count']

def cleanup_old_data():
    """Clean up old database data"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute("""
            DELETE FROM command_usage
            WHERE last_announcement < ?
        """, (seven_days_ago,))
        conn.commit()

# Utility functions
def _build_name(first_name: str | None, last_name: str | None) -> str:
    """Build user display name"""
    if first_name:
        return f"{first_name}{f' {last_name}' if last_name else ''}"
    return "User"

def get_user_mention_html(user) -> str:
    """Generate HTML mention for user"""
    display = _build_name(user.first_name, getattr(user, 'last_name', None))
    return f'<a href="tg://user?id={user.id}">{sanitize_html(display)}</a>'

def get_user_mention_html_from_data(
    user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None
) -> str:
    """Generate HTML mention from stored user data"""
    display = sanitize_html(_build_name(first_name, last_name))
    return f'<a href="tg://user?id={user_id}">{display}</a>'

def format_user_display_name(username: str | None, first_name: str | None, last_name: str | None) -> str:
    """Format a user's display name"""
    return _build_name(first_name, last_name)

# Time utilities
def is_night_time_in_bangladesh() -> bool:
    """Check if it's night time in Bangladesh"""
    bd_tz = pytz.timezone(BANGLADESH_TZ)
    bd_time = datetime.now(bd_tz).time()
    night_start = time(18, 0)  # 6 PM
    night_end = time(6, 0)     # 6 AM
    return bd_time >= night_start or bd_time <= night_end

def get_time_until_night() -> tuple[int, int]:
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

# Random user selection
def select_random_users(users, count=1, exclude=None):
    """Select random users from a list"""
    if exclude is None:
        exclude = []
    available_users = [user for user in users if user['user_id'] not in exclude]
    if len(available_users) < count:
        return available_users
    return random.sample(available_users, count)

def select_random_users_seeded(users, count=1, seed=None, exclude=None):
    """Select random users with a seed for consistent daily selection"""
    if exclude is None:
        exclude = []
    available_users = [user for user in users if user['user_id'] not in exclude]
    if len(available_users) < count:
        return available_users
    if seed:
        random.seed(seed)
    selected = random.sample(available_users, count)
    random.seed()
    return selected

# Leaderboard formatting
def format_aura_leaderboard(leaderboard_data, chat_title=None):
    """Format aura leaderboard message with IShowSpeed energy"""
    if not leaderboard_data:
        return "🔥 <b>AURA LEADERBOARD</b> 🔥\n\n💀 Yo Chat Is Dead... ZERO AURA Detected! SPEED'S Disappointed. Go Touch Grass And Come Back STRONGER 😭💀"

    title = "🏃‍♂️ <b>SIGMA</b> 🏃‍♂️"
    if chat_title:
        title += f" - <b>{chat_title}</b>"
    title += " 🔥\n\n"

    leaderboard_text = title
    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(leaderboard_data):
        position = i + 1
        user_mention = get_user_mention_html_from_data(
            user["user_id"], user["username"], user["first_name"], user["last_name"]
        )
        aura = user["aura_points"]
        if position <= 3:
            medal = medals[position - 1]
            if position == 1:
                leaderboard_text += f"{medal} {user_mention}: <b>{aura}</b> AURA - Yess Sarr! 👑\n"
            else:
                leaderboard_text += f"{medal} {user_mention}: <b>{aura}</b> AURA - W Bro! 💯\n"
        else:
            leaderboard_text += f"🏅 {user_mention}: <b>{aura}</b> AURA\n"

    leaderboard_text += "\n⚡ Yo what are y’all doing?! Run it up! Command after command! GO FASTER, GO LOUDER! 🔥💨"
    return leaderboard_text

# Other helpers
def extract_user_info(user):
    """Extract user information from Telegram user object"""
    return {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': getattr(user, 'last_name', None),
        'is_bot': user.is_bot,
        'language_code': user.language_code
    }

def sanitize_html(text: str) -> str:
    """Sanitize HTML text"""
    import html
    return html.escape(text)

# Handler functions
async def typing_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show typing action"""
    if update.effective_chat:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

async def collect_group_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect group members and administrators"""
    if update.effective_chat.type in ['private']:
        return

    chat_id = update.effective_chat.id
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status in ['administrator', 'creator']:
            try:
                chat_member_count = await context.bot.get_chat_member_count(chat_id)
                logger.info(f"SPEED'S CHAT {chat_id} HAS {chat_member_count} TOTAL MEMBERS! W COUNT! 👥")
                if chat_member_count <= MAX_MEMBERS_PER_BATCH:
                    pass
            except Exception as e:
                logger.warning(f"SPEED COULDN'T GET MEMBER COUNT FOR CHAT {chat_id}: {e}")

        administrators = await context.bot.get_chat_administrators(chat_id)
        for admin in administrators:
            if admin.user and not admin.user.is_bot:
                user_info = extract_user_info(admin.user)
                add_or_update_user(**user_info)
                add_chat_member(chat_id, admin.user.id, admin.status)
        logger.info(f"SPEED COLLECTED {len(administrators)} ADMINISTRATORS FOR CHAT {chat_id}! W COLLECTION! 👑")
    except Exception as e:
        logger.warning(f"SPEED COULDN'T COLLECT GROUP MEMBERS FOR CHAT {chat_id}: {e}")

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new member joining chat"""
    if not update.message or not update.message.new_chat_members:
        return

    chat_id = update.effective_chat.id
    for member in update.message.new_chat_members:
        if not member.is_bot:
            user_info = extract_user_info(member)
            add_or_update_user(**user_info)
            add_chat_member(chat_id, member.id, 'member')
            logger.info(f"SPEED ADDED NEW MEMBER {member.id} TO CHAT {chat_id}! W ADDITION! 🎉")

async def handle_member_left(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member leaving chat"""
    if not update.message or not update.message.left_chat_member:
        return

    chat_id = update.effective_chat.id
    user_id = update.message.left_chat_member.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE chat_members 
        SET status = 'left' 
        WHERE chat_id = ? AND user_id = ?
    ''', (chat_id, user_id))
    conn.commit()
    logger.info(f"SPEED'S MEMBER {user_id} LEFT CHAT {chat_id}! GOODBYE! 👋")

async def track_message_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track user message activity"""
    if not update.effective_user or update.effective_user.is_bot:
        return
    if update.effective_chat.type == 'private':
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    user_info = extract_user_info(user)
    add_or_update_user(**user_info)
    update_member_activity(chat_id, user.id)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        logger.info(f"🔓 SPEED DISABLED BROADCAST MODE FOR {user.id}! W MOVE!")

    # Add user to database
    user_info = extract_user_info(user)
    add_or_update_user(**user_info)

    start_message = f"""
🔥 <b>YOOOO {get_user_mention_html(user)}!!!</b>  
Wassup boiii?! you just pulled up in the OHIO ZONE.

SUUIIIII Cristiano the real GOAT. Luffy is better bro. 

<b>💣 COMMANDS TO GO DUMB:</b>  
├─ 🌈 /gay • Who gay today?  
├─ 😩 /simp • Caught simpin in 4K  
├─ 💞 /couple • Get yo rizz game up  
├─ 💀 /toxic • Demon mode activated  
├─ 🫡 /respect • W HUMAN ALERT  
└─ 📊 /aura • Check yo stats boi

<b>📜 REAL TALK:</b>  
• One drop a day, don’t act hungry  
• Stack that aura like a menace  
• Be LOUD, be WILD, be HIM 💯

YESS SARRR! LEEEEEES FUCKIN GOOOOOOOOO!!!! 🔥
"""

    keyboard = [
        [
            InlineKeyboardButton("Updates", url=UPDATES_CHANNEL),
            InlineKeyboardButton("Chat", url=SUPPORT_GROUP)
        ],
        [
            InlineKeyboardButton("Add Me To Your Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true" if BOT_USERNAME else "https://t.me/iShowNiggaBot?startgroup=true")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        start_message,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )

async def gay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gay command"""
    await handle_single_user_command(update, context, 'gay')

async def couple_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /couple command"""
    await handle_couple_command(update, context)

async def simp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /simp command"""
    await handle_single_user_command(update, context, 'simp')

async def toxic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /toxic command"""
    await handle_single_user_command(update, context, 'toxic')

async def cringe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cringe command"""
    await handle_single_user_command(update, context, 'cringe')

async def respect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /respect command"""
    await handle_single_user_command(update, context, 'respect')

async def sus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sus command"""
    await handle_single_user_command(update, context, 'sus')

async def handle_single_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    """Handle single user selection commands"""
    if not update.effective_user or not update.effective_chat:
        return

    # Only work in groups
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "💀 Yo bro, this ain't for DMs! Add me to a group and let's go crazy with the squad! 🔥⚡"
        )
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    await typing_action(update, context)

    # Add user to database
    user_info = extract_user_info(user)
    add_or_update_user(**user_info)
    update_member_activity(chat_id, user_id)

    can_use, reason = can_use_command(user_id, chat_id, command)

    if not can_use:
        if reason == 'hourly_limit':
            await update.message.reply_text(
                f"⏳ Yo bro! Chill for a hour before hitting /{command} again. Speed says patience is key! 🔥⚡"
            )
        else:
            await update.message.reply_text(
                f"⏳ Nah bro, you already used /{command} today! Come back tomorrow and try again 👑💯"
            )
        return

    # Check if we already have today's selection
    existing_selection = get_daily_selection(chat_id, command)
    if existing_selection:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, first_name, last_name
                FROM users WHERE user_id = ?
            """, (existing_selection['user_id'],))
            selected_user_data = cursor.fetchone()

        if selected_user_data:
            selected_user_mention = get_user_mention_html_from_data(
                existing_selection['user_id'],
                selected_user_data['username'],
                selected_user_data['first_name'],
                selected_user_data['last_name']
            )

            message_template = random.choice(COMMAND_MESSAGES[command])
            final_message = message_template.format(user=selected_user_mention)

            await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
            mark_command_used(user_id, chat_id, command)
            return

    active_members = get_active_chat_members(chat_id)

    if len(active_members) < 1:
        await update.message.reply_text(
            "💀 Yo chat is dead! Speed needs at least someone here to make this work 🔥😭"
        )
        return

    seed = f"{chat_id}_{command}_{date.today().isoformat()}"
    selected_users = select_random_users_seeded(active_members, 1, seed)

    if not selected_users:
        await update.message.reply_text(
            "😬 Bruh, couldn't pick anyone! Try again later when the chat has some energy! 💀"
        )
        return

    selected_user = selected_users[0]

    save_daily_selection(chat_id, command, selected_user['user_id'])

    aura_change = AURA_POINTS[command]
    update_aura_points(selected_user['user_id'], aura_change)

    selected_user_mention = get_user_mention_html_from_data(
        selected_user['user_id'],
        selected_user['username'],
        selected_user['first_name'],
        selected_user['last_name']
    )

    message_template = random.choice(COMMAND_MESSAGES[command])
    final_message = message_template.format(user=selected_user_mention)

    if aura_change > 0:
        final_message += f"\n\n🔥 <b>+{aura_change} Aura Points! That’s how you do it, bitch!</b> 👑💯"
    else:
        final_message += f"\n\n💀 <b>Lost {aura_change} Aura points? Bruh, at this rate, even ghosts got more aura than you!</b> 😂"

    await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
    mark_command_used(user_id, chat_id, command)

async def handle_couple_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle couple command logic"""
    if not update.effective_user or not update.effective_chat:
        return
    
    # Only work in groups
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "💀 Yo bro, this ain't for DMs! Add me to a group and let's find some couples! 🔥💑"
        )
        return
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    command = 'couple'
    
    await typing_action(update, context)
    
    # Add user to database
    user_info = extract_user_info(user)
    add_or_update_user(**user_info)
    update_member_activity(chat_id, user_id)
    
    # Check if user can use command
    can_use, reason = can_use_command(user_id, chat_id, command)
    
    if not can_use:
        if reason == 'hourly_limit':
            await update.message.reply_text(
                f"⏳ Yo bro! Chill for a hour before hitting /{command} again. Speed says patience is key! 🔥⚡"
            )
        else:
            await update.message.reply_text(
                f"⏳ Nah bro, you already used /{command} today! Come back tomorrow and try again 👑💯"
            )
        return
    
    # Check if we already have today's selection
    existing_selection = get_daily_selection(chat_id, command)
    if existing_selection:
        # Get user data for both users
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, first_name, last_name
                FROM users WHERE user_id = ?
            """, (existing_selection['user_id'],))
            user1_data = cursor.fetchone()
            
            cursor.execute("""
                SELECT username, first_name, last_name
                FROM users WHERE user_id = ?
            """, (existing_selection['user_id_2'],))
            user2_data = cursor.fetchone()
        
        if user1_data and user2_data:
            user1_mention = get_user_mention_html_from_data(
                existing_selection['user_id'],
                user1_data['username'],
                user1_data['first_name'],
                user1_data['last_name']
            )
            user2_mention = get_user_mention_html_from_data(
                existing_selection['user_id_2'],
                user2_data['username'],
                user2_data['first_name'],
                user2_data['last_name']
            )
            
            # Choose random message
            message_template = random.choice(COMMAND_MESSAGES[command])
            final_message = message_template.format(user1=user1_mention, user2=user2_mention)
            
            await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
            mark_command_used(user_id, chat_id, command)
            return
    
    # Get active chat members
    active_members = get_active_chat_members(chat_id)
    
    if len(active_members) < 2:
        await update.message.reply_text(
            "💀 Yo chat is dead! Speed needs at least 2 people to make this work! Where everybody at?! 🔥😭"
        )
        return
    
    # Select 2 random users using seeded selection for consistency
    seed = f"{chat_id}_{command}_{date.today().isoformat()}"
    selected_users = select_random_users_seeded(active_members, 2, seed)
    
    if len(selected_users) < 2:
        await update.message.reply_text(
            "😭 Yo, couldn't find 2 people! Chat needs more energy, try again later! 💀🔥"
        )
        return
    
    user1, user2 = selected_users
    
    # Save selection
    save_daily_selection(chat_id, command, user1['user_id'], user2['user_id'])
    
    # Update aura points for both users
    aura_change = AURA_POINTS[command]
    update_aura_points(user1['user_id'], aura_change)
    update_aura_points(user2['user_id'], aura_change)
    
    # Create mentions
    user1_mention = get_user_mention_html_from_data(
        user1['user_id'], user1['username'], user1['first_name'], user1['last_name']
    )
    user2_mention = get_user_mention_html_from_data(
        user2['user_id'], user2['username'], user2['first_name'], user2['last_name']
    )
    
    # Choose random message and send
    message_template = random.choice(COMMAND_MESSAGES[command])
    final_message = message_template.format(user1=user1_mention, user2=user2_mention)
    
    # Add aura change info
    final_message += f"\n\n🫶 <b>Duo just earned +{aura_change} Aura! Love stats going CRAZY 📈💘</b>"
    
    await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
    mark_command_used(user_id, chat_id, command)

async def ghost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ghost command (night time only)"""
    if not update.effective_user or not update.effective_chat:
        return
    
    # Only work in groups
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "💀 Yo bro, this ain't for DMs! Add me to a group and let's get spooky! 👻🔥"
        )
        return
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    command = 'ghost'
    
    await typing_action(update, context)
    
    # Check if it's night time in Bangladesh
    if not is_night_time_in_bangladesh():
        hours, minutes = get_time_until_night()
        await update.message.reply_text(
            f"🌙 Yo ghost mode is only 6 PM to 6 AM BD time!\n\n⏰ Wait {hours}h {minutes}m and then we can get spooky! 👻🔥"
        )
        return
    
    # Add user to database
    user_info = extract_user_info(user)
    add_or_update_user(**user_info)
    update_member_activity(chat_id, user_id)
    
    # Check if user can use command
    can_use, reason = can_use_command(user_id, chat_id, command)
    
    if not can_use:
        if reason == 'hourly_limit':
            await update.message.reply_text(
                f"⏰ Chill the hell out, nigga! Wait an hour or get faded by the shadows 👻💀"
            )
        else:
            await update.message.reply_text(
                f"👻 Ghost’s already out today! Wait till tomorrow or get fucked up, nigga 💀"
            )
        return
    
    # Check if we already have today's selection
    existing_selection = get_daily_selection(chat_id, command)
    if existing_selection:
        # Get user data for the existing selection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, first_name, last_name
                FROM users WHERE user_id = ?
            """, (existing_selection['user_id'],))
            selected_user_data = cursor.fetchone()
        
        if selected_user_data:
            selected_user_mention = get_user_mention_html_from_data(
                existing_selection['user_id'],
                selected_user_data['username'],
                selected_user_data['first_name'],
                selected_user_data['last_name']
            )
            
            # Choose random message
            message_template = random.choice(COMMAND_MESSAGES[command])
            final_message = message_template.format(user=selected_user_mention)
            
            await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
            mark_command_used(user_id, chat_id, command)
            return
    
    # Get active chat members
    active_members = get_active_chat_members(chat_id)
    
    if len(active_members) < 1:
        await update.message.reply_text(
            "💀 Chat dead as hell. Where y’all at fam? Pull up with the squad and turn this shit up! 😭🔥"
        )
        return
    
    # Select random user using seeded selection for consistency
    seed = f"{chat_id}_{command}_{date.today().isoformat()}"
    selected_users = select_random_users_seeded(active_members, 1, seed)
    
    if not selected_users:
        await update.message.reply_text(
            "😭 Spirits showed up and dipped. Chat was dead, vibe was trash. Come back when it’s lit! 👻🔥"
        )
        return
    
    selected_user = selected_users[0]
    
    # Save selection
    save_daily_selection(chat_id, command, selected_user['user_id'])
    
    # Update aura points
    aura_change = AURA_POINTS[command]
    update_aura_points(selected_user['user_id'], aura_change)
    
    # Create mention
    selected_user_mention = get_user_mention_html_from_data(
        selected_user['user_id'],
        selected_user['username'],
        selected_user['first_name'],
        selected_user['last_name']
    )
    
    # Choose random message and send
    message_template = random.choice(COMMAND_MESSAGES[command])
    final_message = message_template.format(user=selected_user_mention)
    
    # Add aura change info
    final_message += f"\n\n💀 <b>{aura_change} Aura gone. Spirits saw your ass and dipped.</b> 👻📉"
    
    await update.message.reply_text(final_message, parse_mode=ParseMode.HTML)
    mark_command_used(user_id, chat_id, command)

async def aura_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /aura command (show leaderboard)"""
    if not update.effective_chat:
        return
    
    # Only work in groups
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "💀 Yo bro, this ain't for DMs! Add me to a group and let's go crazy with the squad! 🔥⚡"
        )
        return
    
    chat_id = update.effective_chat.id
    
    await typing_action(update, context)
    
    # Get leaderboard
    leaderboard_data = get_leaderboard(chat_id, 10)
    
    # Get chat title if available
    chat_title = getattr(update.effective_chat, 'title', None)
    
    # Format and send leaderboard
    leaderboard_message = format_aura_leaderboard(leaderboard_data, chat_title)
    
    await update.message.reply_text(
        leaderboard_message,
        parse_mode=ParseMode.HTML
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command (owner only)"""
    user_info = extract_user_info(update.message.from_user)
    logger.info(f"📢 SPEED'S BROADCAST COMMAND ATTEMPTED BY {user_info.get('full_name', 'Unknown')}!")

    if not update.message.from_user or update.message.from_user.id != OWNER_ID:
        logger.warning(f"🚫 SPEED'S UNAUTHORIZED BROADCAST ATTEMPT BY USER {update.message.from_user.id if update.message.from_user else 'Unknown'}!")
        await typing_action(update, context)
        response = await update.message.reply_text("⛔ This command is restricted.")
        logger.info(f"⚠️ SPEED'S UNAUTHORIZED ACCESS MESSAGE SENT, ID: {response.message_id}!")
        return

    await typing_action(update, context)

    # Get user and group counts
    user_ids = get_all_users()
    group_ids = get_all_groups()

    # Create inline keyboard for broadcast target selection
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"👥 Users ({len(user_ids)})", callback_data="broadcast_users"),
            InlineKeyboardButton(f"📢 Groups ({len(group_ids)})", callback_data="broadcast_groups")
        ]
    ])

    response = await update.message.reply_text(
        "📣 <b>Choose broadcast target:</b>\n\n"
        f"👥 <b>Users:</b> {len(user_ids)} individual users\n"
        f"📢 <b>Groups:</b> {len(group_ids)} groups\n\n"
        "Select where you want to send your broadcast message:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    logger.info(f"✅ Broadcast target selection sent, message ID: {response.message_id}")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ping command"""
    import time
    start_time = time.time()
    await typing_action(update, context)
    end_time = time.time()
    response_time = round((end_time - start_time) * 1000, 2)
    await update.message.reply_text(
        f'⚡ <a href="{SUPPORT_GROUP}">BOOM!</a> {response_time}ms',
        parse_mode=ParseMode.HTML
    )

async def handle_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast target selection callback"""
    query = update.callback_query
    await query.answer()
    
    if not query.from_user or query.from_user.id != OWNER_ID:
        await query.answer("⛔ This command is restricted.", show_alert=True)
        return
    
    if query.data.startswith('broadcast_'):
        target = query.data.split('_')[1]  # 'users' or 'groups'
        broadcast_target[query.from_user.id] = target
        broadcast_mode.add(query.from_user.id)
        
        logger.info(f"👑 Enabling broadcast mode for owner {query.from_user.id} - Target: {target}")
        
        target_text = "individual users" if target == "users" else "groups"
        user_ids = get_all_users()
        group_ids = get_all_groups()
        target_count = len(user_ids) if target == "users" else len(group_ids)
        
        try:
            await query.edit_message_text(
                text=f"📣 <b>SPEED'S BROADCAST MODE ENABLED!</b>\n\n"
                f"🎯 <b>Target:</b> {target_text} ({target_count})\n\n"
                "Send me any message and I will forward it to all selected targets.",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"❌ SPEED'S BROADCAST MESSAGE EDIT FAILED: {e}")

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message sending"""
    if not update.message.from_user or update.message.from_user.id not in broadcast_mode:
        return
    
    if update.message.chat.type != "private":
        return
    
    logger.info(f"📢 Broadcasting message from owner {update.message.from_user.id}")
    
    target = broadcast_target.get(update.message.from_user.id, "users")
    user_ids = get_all_users()
    group_ids = get_all_groups()
    target_list = user_ids if target == "users" else group_ids
    
    success_count = 0
    failed_count = 0
    
    for target_id in target_list:
        try:
            await context.bot.copy_message(
                chat_id=target_id,
                from_chat_id=update.message.chat.id,
                message_id=update.message.message_id
            )
            success_count += 1
            logger.info(f"✅ Message sent to {target_id}")
        except Exception as e:
            failed_count += 1
            logger.warning(f"❌ Failed to send to {target_id}: {e}")
    
    # Send broadcast summary
    await update.message.reply_text(
        f"📊 <b>Broadcast Summary:</b>\n\n"
        f"✅ <b>Sent:</b> {success_count}\n"
        f"❌ <b>Failed:</b> {failed_count}\n"
        f"🎯 <b>Target:</b> {target}\n\n"
        "Broadcast mode is still active. Send another message or use /start to disable.",
        parse_mode=ParseMode.HTML
    )
    
    # Remove from broadcast mode after sending
    broadcast_mode.discard(update.message.from_user.id)
    if update.message.from_user.id in broadcast_target:
        del broadcast_target[update.message.from_user.id]
    
    logger.info(f"🔓 SPEED'S BROADCAST MODE DISABLED FOR {update.message.from_user.id}!")

async def cleanup_expired_data(context: ContextTypes.DEFAULT_TYPE):
    """Periodic cleanup function"""
    try:
        cleanup_old_data()
        logger.info("SPEED'S DATABASE CLEANUP COMPLETED! W MAINTENANCE! 🧹")
    except Exception as e:
        logger.error(f"SPEED'S DATABASE CLEANUP FAILED: {e}")

def setup_periodic_jobs(application):
    """Setup periodic jobs for the application"""
    try:
        job_queue = application.job_queue
        if job_queue:
            # Run database cleanup every 24 hours
            job_queue.run_repeating(
                cleanup_expired_data,
                interval=timedelta(hours=24),
                first=timedelta(minutes=1)
            )
            logger.info("SPEED'S PERIODIC JOBS SETUP SUCCESSFULLY! W AUTOMATION! ⚡")
        else:
            logger.warning("SPEED'S JOB QUEUE NOT AVAILABLE! PERIODIC CLEANUP DISABLED!")
    except Exception as e:
        logger.warning(f"SPEED'S PERIODIC JOBS SETUP FAILED: {e}")

async def on_startup(application: Application) -> None:
    """Initialize bot on startup"""
    global BOT_USERNAME
    
    # Get bot info to set username dynamically
    try:
        bot_info = await application.bot.get_me()
        BOT_USERNAME = bot_info.username
        logger.info(f"SPEED'S BOT USERNAME SET: @{BOT_USERNAME} - LET'S GOOO! 🔥")
    except Exception as e:
        logger.error(f"SPEED'S BOT INFO FAILED: {e}")
        BOT_USERNAME = "iShowNiggaBot"
    
    commands = [
           BotCommand("start", "🔥 Speed's Bot"),
            BotCommand("gay", "🏳️‍🌈 Who's Gay"),
            BotCommand("couple", "💞 Find Love"),
            BotCommand("simp", "🥺 Simp Alert"),
            BotCommand("toxic", "☠️ Toxic Check"),
            BotCommand("cringe", "😬 Cringe Meter"),
            BotCommand("respect", "🫡 Respect Points"),
           BotCommand("sus", "👀 Sus Detector"),
            BotCommand("ghost", "👻 Ghost Mode"),
            BotCommand("aura", "📈 Aura Check"),
]
    
    await application.bot.set_my_commands(commands)
    logger.info("SPEED'S COMMANDS REGISTERED SUCCESSFULLY! W SETUP! 💯")

# HTTP server for health checks
class SpeedHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SPEED'S BOT IS ALIVE AND GRINDING!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def start_speed_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SpeedHandler)
    print(f"SPEED'S SERVER LISTENING ON PORT {port} - LET'S GOOO! 🔥")
    server.serve_forever()

def main():
    """Main function to start the bot"""
    init_database()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("gay", gay_command))
    application.add_handler(CommandHandler("couple", couple_command))
    application.add_handler(CommandHandler("simp", simp_command))
    application.add_handler(CommandHandler("toxic", toxic_command))
    application.add_handler(CommandHandler("cringe", cringe_command))
    application.add_handler(CommandHandler("respect", respect_command))
    application.add_handler(CommandHandler("sus", sus_command))
    application.add_handler(CommandHandler("ghost", ghost_command))
    application.add_handler(CommandHandler("aura", aura_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("ping", ping_command))
    
    # Add callback query handler for broadcast
    application.add_handler(CallbackQueryHandler(handle_broadcast_callback))
    
    # Add member tracking handlers
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, 
        handle_new_member
    ))
    application.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER, 
        handle_member_left
    ))
    
    # Handle broadcast messages in private chat
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & ~filters.COMMAND,
        handle_broadcast_message
    ))
    
    # Track all messages for activity
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        track_message_activity
    ))
    
    # Setup periodic jobs
    setup_periodic_jobs(application)
    
    # Register startup hook
    application.post_init = on_startup
    
    # Start the bot
    logger.info("SPEED'S TELEGRAM AURA BOT STARTING - LET'S GOOO! 🚀")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    # Start HTTP server for health checks
    threading.Thread(target=start_speed_server, daemon=True).start()
    main()