# ============================================================
#  🚀 Leon Link Bypass Bot — FINAL
#  Bot: @Leonbypassbot | Admin: 8626080388 | Owner: @I339b
# ============================================================

import re
import html
import time
import sqlite3
import asyncio
import logging
import os
import requests
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN", "9238725804:AAGSrY4BnNohMRsgEWCHJ3_wHE7AJqkGsXI").strip()
ADMIN_ID = 8626080388
BOT_LINK = "https://t.me/Leonbypassbot"
OWNER_USERNAME = "@I339b"
OWNER_LINK = "https://t.me/I339b"

API_BASE = "https://altaf-api-maker.base44.app/functions/lookup?tool=shortner-bypass&key=Bypass&q="
DB_FILE = os.getenv("DB_FILE", "leon_bypass.db").strip() or "leon_bypass.db"

# Force Join Channel Configuration
REQUIRED_CHANNELS = [
    {"username": "sterniterspro", "title": "Sterniters Pro", "url": "https://t.me/sterniterspro"},
]

CREDIT_START = 10
REFERRAL_REWARD = 15
REFERRAL_BONUS_NEW = 5
CREDIT_PER_LOOKUP = 1

START_TIME = time.time()

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

HTTP_SESSION = requests.Session()
HTTP_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
})

# ================== FONTS ==================
def b(text):
    out = []
    for c in str(text):
        if 'A' <= c <= 'Z': out.append(chr(0x1D400 + ord(c) - 65))
        elif 'a' <= c <= 'z': out.append(chr(0x1D41A + ord(c) - 97))
        elif '0' <= c <= '9': out.append(chr(0x1D7CE + ord(c) - 48))
        else: out.append(c)
    return "".join(out)

def sc(text):
    m = {'a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ','i':'ɪ',
         'j':'ᴊ','k':'ᴋ','l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴘ','q':'ǫ','r':'ʀ',
         's':'ꜱ','t':'ᴛ','u':'ᴜ','v':'ᴠ','w':'ᴡ','x':'x','y':'ʏ','z':'ᴢ'}
    return "".join(m.get(c.lower(), c) for c in str(text))

def H(value):
    if value is None: return "—"
    s = str(value).strip()
    if not s or s.lower() in ("null", "none"): return "—"
    s = html.escape(s, quote=False)
    return s.replace("<", "‹").replace(">", "›")[:400]

# ================== ANIMATION ==================
LOADING_BARS = [
    "▱▱▱▱▱▱▱▱▱▱", "▰▱▱▱▱▱▱▱▱▱", "▰▰▱▱▱▱▱▱▱▱",
    "▰▰▰▱▱▱▱▱▱▱", "▰▰▰▰▱▱▱▱▱▱", "▰▰▰▰▰▱▱▱▱▱",
    "▰▰▰▰▰▰▱▱▱▱", "▰▰▰▰▰▰▰▱▱▱", "▰▰▰▰▰▰▰▰▱▱",
    "▰▰▰▰▰▰▰▰▰▱", "▰▰▰▰▰▰▰▰▰▰",
]

def progress_bar(pct):
    return LOADING_BARS[min(max(int(pct / 10), 0), 10)]

ANIM_STEPS = [
    (20, "⚡", "Initializing Bypass Engine", "Establishing secure connection..."),
    (45, "🛰️", "Processing Short Link", "Extracting hidden destination..."),
    (70, "🔍", "Bypassing Gateway", "Solving redirects and tokens..."),
    (90, "🧬", "Decrypting Destination", "Finalizing real URL..."),
    (100, "✅", "Bypass Complete", "Rendering output..."),
]

def thinking_msg(step=0, query=""):
    idx = min(max(step, 0), len(ANIM_STEPS) - 1)
    pct, icon, stage, detail = ANIM_STEPS[idx]
    q_line = f"🔗 <b>{b('Input Link')}</b> : {H(query)}\n\n" if query else ""
    return (
        f"🚀  <b>{b('Leon Link Bypass')}</b>  🚀\n\n"
        f"{q_line}"
        f"{icon} <b>{b(stage)}...</b>\n"
        f"<i>{detail}</i>\n\n"
        f"<code>[{progress_bar(pct)}] {pct}%</code>\n\n"
        f"⏳ <b>{sc('Please wait')}...</b>"
    )

# ================== DATABASE ==================
def db_init():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        credits INTEGER DEFAULT 0, referred_by INTEGER,
        referral_count INTEGER DEFAULT 0, total_lookups INTEGER DEFAULT 0,
        joined_at INTEGER, last_seen INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE, title TEXT, added_at INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS redeem_codes (
        code TEXT PRIMARY KEY, credits INTEGER, max_uses INTEGER,
        used_count INTEGER DEFAULT 0, created_by INTEGER, created_at INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS code_usage (
        code TEXT, user_id INTEGER, used_at INTEGER,
        PRIMARY KEY (code, user_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS join_verified (
        user_id INTEGER PRIMARY KEY, verified_at INTEGER)""")
    conn.commit()
    conn.close()

db_init()

def db_exec(sql, params=()):
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute(sql, params); conn.commit(); conn.close()

def db_fetch(sql, params=()):
    conn = sqlite3.connect(DB_FILE); conn.row_factory = sqlite3.Row
    c = conn.cursor(); c.execute(sql, params); rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def db_one(sql, params=()):
    rows = db_fetch(sql, params)
    return rows[0] if rows else None

def get_user(uid): return db_one("SELECT * FROM users WHERE user_id=?", (uid,))

def create_user(uid, uname, fname, referred_by=None):
    now = int(time.time())
    db_exec("""INSERT OR IGNORE INTO users
               (user_id, username, first_name, credits, referred_by, joined_at, last_seen)
               VALUES (?,?,?,?,?,?,?)""",
            (uid, uname, fname, CREDIT_START, referred_by, now, now))

def add_credits(uid, amount):
    db_exec("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount, uid))

def use_credits(uid, amount):
    u = get_user(uid)
    if not u or u["credits"] < amount: return False
    db_exec("UPDATE users SET credits = credits - ? WHERE user_id=?", (amount, uid))
    return True

def inc_lookup(uid):
    db_exec("UPDATE users SET total_lookups = total_lookups + 1, last_seen = ? WHERE user_id=?",
            (int(time.time()), uid))

def inc_referral(uid):
    db_exec("UPDATE users SET referral_count = referral_count + 1 WHERE user_id=?", (uid,))

def get_admin_channels():
    return db_fetch("SELECT * FROM channels ORDER BY id")

def add_channel(uname, title):
    uname = uname.lower().replace("@", "").strip()
    db_exec("INSERT OR IGNORE INTO channels (username, title, added_at) VALUES (?,?,?)",
            (uname, title, int(time.time())))

def remove_channel(uname):
    db_exec("DELETE FROM channels WHERE username=?", (uname.lower().replace("@", ""),))

def create_code(code, credits, max_uses, created_by):
    try:
        db_exec("INSERT INTO redeem_codes (code, credits, max_uses, created_by, created_at) VALUES (?,?,?,?,?)",
                (code.upper(), credits, max_uses, created_by, int(time.time())))
        return True
    except: return False

def get_code(code): return db_one("SELECT * FROM redeem_codes WHERE code=?", (code.upper(),))

def use_code(code, uid):
    c = get_code(code)
    if not c: return "invalid"
    if c["used_count"] >= c["max_uses"]: return "full"
    if db_one("SELECT * FROM code_usage WHERE code=? AND user_id=?", (code.upper(), uid)): return "already"
    db_exec("INSERT INTO code_usage (code, user_id, used_at) VALUES (?,?,?)", (code.upper(), uid, int(time.time())))
    db_exec("UPDATE redeem_codes SET used_count = used_count + 1 WHERE code=?", (code.upper(),))
    add_credits(uid, c["credits"])
    return c["credits"]

def list_codes(): return db_fetch("SELECT * FROM redeem_codes ORDER BY created_at DESC")
def total_users(): r = db_one("SELECT COUNT(*) as n FROM users"); return r["n"] if r else 0

def mark_join_verified(uid):
    db_exec("INSERT OR REPLACE INTO join_verified (user_id, verified_at) VALUES (?, ?)", (uid, int(time.time())))

def is_join_verified(uid):
    r = db_one("SELECT * FROM join_verified WHERE user_id=?", (uid,))
    return bool(r and (int(time.time()) - r["verified_at"]) < 3600)

# ================== FORCE JOIN ==================
async def get_missing_channels(bot, uid):
    missing = []
    for ch in REQUIRED_CHANNELS:
        try:
            m = await bot.get_chat_member(chat_id=f"@{ch['username']}", user_id=uid)
            if m.status not in ("member", "administrator", "creator", "restricted"): 
                missing.append(ch)
        except Exception:
            missing.append(ch)
    return missing

def force_join_kb():
    rows = [[InlineKeyboardButton(f"📢 Join {ch['title']}", url=ch["url"])] for ch in REQUIRED_CHANNELS]
    rows.append([InlineKeyboardButton("✅ I Joined All", callback_data="check_join_now")])
    return InlineKeyboardMarkup(rows)

def force_join_msg():
    return (
        f"🔒  <b>{b('Join Required')}</b>  🔒\n\n"
        f"👋 Bot use karne se pehle\n"
        f"channel join karna zaroori hai\n\n"
        f"📢 <b>{b('Required Channel')}</b> :\n"
        f"  🔗 @sterniterspro\n\n"
        f"👇 Neeche button se join karo\n"
        f"Phir ✅ <b>I Joined All</b> dabao"
    )

# ================== BUTTONS ==================
def btn(text, **kw):
    kw.pop('style', None) 
    return InlineKeyboardButton(text, **kw)

def main_menu_kb():
    return InlineKeyboardMarkup([
        [btn("🔗 " + sc("Bypass Link"), callback_data="new_lookup")],
        [btn("💎 " + sc("My Credits"), callback_data="my_credits"),
         btn("🎁 " + sc("Referral"), callback_data="my_referral")],
        [btn("🎟️ " + sc("Redeem Code"), callback_data="redeem_prompt"),
         btn("📖 " + sc("Help"), callback_data="menu_help")],
        [btn("👑 " + sc("Owner"), url=OWNER_LINK),
         btn("❌ " + sc("Close"), callback_data="close_menu")],
    ])

def back_kb(): return InlineKeyboardMarkup([[btn("⬅️ " + sc("Back"), callback_data="main_menu")]])

def result_kb():
    return InlineKeyboardMarkup([
        [btn("🔍 " + sc("New Bypass"), callback_data="new_lookup"),
         btn("🏠 " + sc("Menu"), callback_data="main_menu")],
        [btn("👑 " + sc("Owner"), url=OWNER_LINK)]])

def admin_kb():
    return InlineKeyboardMarkup([
        [btn("📊 " + sc("Stats"), callback_data="a_stats"), btn("📢 " + sc("Channels"), callback_data="a_channels")],
        [btn("🎟️ " + sc("Create Code"), callback_data="a_code_create"), btn("📋 " + sc("List Codes"), callback_data="a_code_list")],
        [btn("📣 " + sc("Broadcast"), callback_data="a_broadcast"), btn("❌ " + sc("Close"), callback_data="a_close")]])

def channels_kb():
    return InlineKeyboardMarkup([
        [btn("➕ " + sc("Add Channel"), callback_data="a_ch_add"), btn("➖ " + sc("Remove Channel"), callback_data="a_ch_remove")],
        [btn("📋 " + sc("List Channels"), callback_data="a_ch_list"), btn("⬅️ " + sc("Back"), callback_data="a_back")]])

def owner_footer():
    return (f"\n\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>{b('Owner')}</b> : {OWNER_USERNAME}\n"
            f"🤖 <b>{b('Bot')}</b> : @Leonbypassbot")

# ================== MESSAGES ==================
def welcome_msg(uid):
    u = get_user(uid) or {}
    return (
        f"🚀  <b>{b('Leon Link Bypass')}</b>  🚀\n\n"
        f"👋 <b>{b('Namaste')}</b>, <b>{H(u.get('first_name') or 'Dost')}</b>!\n\n"
        f"Main ek advanced Link Bypass bot hoon.\n"
        f"Kisi bhi annoying shortener link ko bhejo, aur\n"
        f"main uska direct destination nikal dunga.\n\n"
        f"💎 <b>{b('Credits')}</b> : <b>{u.get('credits', 0)}</b>\n"
        f"🎁 <b>{b('Referrals')}</b> : <b>{u.get('referral_count', 0)}</b>\n\n"
        f"👇 Seedha chat me link bhejo ya menu use karo!{owner_footer()}")

def help_msg():
    return (
        f"📖  <b>{b('Help Menu')}</b>  📖\n\n"
        f"🔗 <b>{b('HOW TO BYPASS')}</b>\n"
        f"Bas koi bhi link copy karo aur chat me paste kardo.\n"
        f"Example: <code>https://gplinks.co/XYZ</code>\n\n"
        f"🎟️ <b>{b('REDEEM')}</b> : <code>/redeem CODE</code>\n"
        f"🎁 <b>{b('REFERRAL')}</b> : <code>/refer</code>\n"
        f"💎 <b>{b('CREDITS')}</b> : <code>/credits</code>\n\n"
        f"💡 Har bypass ka 1 credit lagta hai.{owner_footer()}")

def credits_msg(uid):
    u = get_user(uid) or {}
    return (
        f"💎  <b>{b('My Credits')}</b>  💎\n\n"
        f"💎 <b>{b('Balance')}</b> : <b>{u.get('credits', 0)}</b>\n"
        f"📊 <b>{b('Total Bypassed')}</b> : {u.get('total_lookups', 0)}\n"
        f"🎁 <b>{b('Referrals')}</b> : {u.get('referral_count', 0)}\n\n"
        f"Har lookup me 1 credit lagta hai.\n"
        f"Referral se 15 credits milte hain.{owner_footer()}")

def referral_msg(uid, bot_username):
    u = get_user(uid) or {}
    link = f"https://t.me/{bot_username}?start=ref_{uid}"
    return (
        f"🎁  <b>{b('Referral Program')}</b>  🎁\n\n"
        f"🔗 <b>{b('Your Link')}</b> :\n"
        f"<code>{H(link)}</code>\n\n"
        f"💰 <b>{b('Rewards')}</b> :\n"
        f"  Naye user ko : +{REFERRAL_BONUS_NEW}\n"
        f"  Tumhe : +{REFERRAL_REWARD}\n\n"
        f"🎁 <b>{b('Your Referrals')}</b> : {u.get('referral_count', 0)}\n\n"
        f"Link share karo aur credits kamao!{owner_footer()}")

def error_msg(reason=""):
    r = f"\n💡 {H(reason)}" if reason else ""
    return (f"❌  <b>{b('Oops! Kuch galat ho gaya')}</b>  ❌{r}\n\n"
            f"🔁 Dubara try karo.{owner_footer()}")

def no_credits_msg():
    return (f"💔  <b>{b('Insufficient Credits')}</b>  💔\n\n"
            f"Tumhare paas <b>0 credits</b> bache hain.\n\n"
            f"🎁 <b>{b('Credits kaise payein:')}</b>\n"
            f"  🎟️ Redeem code use karo\n"
            f"  🎁 Referral share karo (+15)\n"
            f"  👑 Admin se contact karo{owner_footer()}")

# ================== API & SMART PARSER ==================
def extract_bypass_result(data, original_query):
    """Recursively finds all URLs and returns the first one that doesn't match the original query."""
    if not data: return None
    found_urls = []
    
    def search_obj(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and v.startswith("http"):
                    found_urls.append(v)
                elif isinstance(v, (dict, list)):
                    search_obj(v)
        elif isinstance(obj, list):
            for item in obj:
                search_obj(item)
        elif isinstance(obj, str):
            urls = re.findall(r'(https?://[^\s"\'>]+)', obj)
            found_urls.extend(urls)
            
    search_obj(data)
    
    # Fallback string regex check
    if isinstance(data, str):
        urls = re.findall(r'(https?://[^\s"\'>]+)', data)
        found_urls.extend(urls)
        
    for url in found_urls:
        clean_url = url.strip()
        # Ignore the original short URL to prevent "Reason: original_link" error
        if clean_url != original_query and len(clean_url) > 10:
            return clean_url
            
    return None

def api_call(query):
    encoded_url = quote(query)
    target = f"{API_BASE}{encoded_url}"
    try:
        r = HTTP_SESSION.get(target, timeout=20)
        if r.status_code in [200, 201]:
            try: return r.json()
            except: return r.text
    except Exception as e:
        logger.error(f"API Bypass error: {e}")
    return None

# ================== SAFE SEND/EDIT ==================
def plain_strip(text): return re.sub(r"<[^>]+>", "", str(text))

async def send_html(bot, chat_id, text, **kwargs):
    try: return await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML, **kwargs)
    except: return await bot.send_message(chat_id, plain_strip(text), **kwargs)

async def edit_q(q, text, **kwargs):
    try: return await q.edit_message_text(text=text, parse_mode=ParseMode.HTML, **kwargs)
    except: return await q.edit_message_text(text=plain_strip(text), **kwargs)

async def edit_message_html(bot, chat_id, message_id, text, **kwargs):
    try: return await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode=ParseMode.HTML, **kwargs)
    except: return await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=plain_strip(text), **kwargs)

# ================== COMMANDS & LOGIC ==================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = update.effective_user

    referred_by = None
    if context.args and context.args[0].startswith("ref_"):
        try:
            ref_id = int(context.args[0][4:])
            if ref_id != user.id: referred_by = ref_id
        except: pass

    existing = get_user(user.id)
    is_new = existing is None

    if is_new:
        create_user(user.id, user.username or "", user.first_name or "", referred_by)
        if referred_by:
            add_credits(referred_by, REFERRAL_REWARD)
            inc_referral(referred_by)
            add_credits(user.id, REFERRAL_BONUS_NEW)
            try:
                await send_html(context.bot, referred_by, f"🎁 <b>{b('New Referral!')}</b>\n\n👤 {H(user.first_name)} ne tumhara link use kiya\n💰 Tumhe <b>+{REFERRAL_REWARD}</b> credits mile! 🎉")
            except: pass
    else:
        db_exec("UPDATE users SET last_seen=?, username=?, first_name=? WHERE user_id=?", (int(time.time()), user.username or "", user.first_name or "", user.id))

    if user.id != ADMIN_ID:
        if await get_missing_channels(context.bot, user.id):
            await send_html(context.bot, msg.chat_id, force_join_msg(), reply_markup=force_join_kb())
            return

    if is_new:
        u = get_user(user.id)
        text = (f"🎉  <b>{b('Welcome!')}</b>  🎉\n\n"
                f"👋 <b>{b('Namaste')}</b> {H(user.first_name)}!\n\n"
                f"✅ <b>{b('Account created!')}</b>\n\n"
                f"💎 <b>{b('Starting Credits')}</b> : {CREDIT_START}\n")
        if referred_by: text += f"🎁 <b>{b('Referral Bonus')}</b> : +{REFERRAL_BONUS_NEW}\n"
        text += f"\n🎯 <b>{b('Total Credits')}</b> : {u.get('credits', CREDIT_START)}\n\nAb bot use kar sakte ho!{owner_footer()}"
        await send_html(context.bot, msg.chat_id, text, reply_markup=main_menu_kb(), disable_web_page_preview=True)
    else:
        await send_html(context.bot, msg.chat_id, welcome_msg(user.id), reply_markup=main_menu_kb(), disable_web_page_preview=True)


async def do_bypass(update, context, query):
    msg = update.message
    user = update.effective_user

    if not get_user(user.id): create_user(user.id, user.username or "", user.first_name or "")

    if user.id != ADMIN_ID:
        if await get_missing_channels(context.bot, user.id):
            await send_html(context.bot, msg.chat_id, force_join_msg(), reply_markup=force_join_kb())
            return

    if not use_credits(user.id, CREDIT_PER_LOOKUP):
        await send_html(context.bot, msg.chat_id, no_credits_msg())
        return

    inc_lookup(user.id)
    try: await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
    except: pass

    status = await send_html(context.bot, msg.chat_id, thinking_msg(0, query))
    if not status: return

    api_task = asyncio.create_task(asyncio.to_thread(api_call, query))
    current_step = 1

    while not api_task.done() and current_step < 4:
        await asyncio.sleep(0.5)
        if not api_task.done():
            try: await status.edit_text(thinking_msg(current_step, query), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            except: pass
            current_step += 1

    while current_step < 5:
        try: await status.edit_text(thinking_msg(current_step, query), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except: pass
        current_step += 1
        await asyncio.sleep(0.2)

    data = None
    try: data = await api_task
    except: pass

    if not data:
        add_credits(user.id, CREDIT_PER_LOOKUP)
        await edit_message_html(context.bot, msg.chat_id, status.message_id, error_msg("Bypass failed. Server timeout ya issue. Credit refunded."), reply_markup=result_kb())
        return

    bypassed_url = extract_bypass_result(data, query)
    
    if not bypassed_url:
        add_credits(user.id, CREDIT_PER_LOOKUP)
        err_reason = "Server ko hidden link nahi mila ya unsupported shortener hai."
        await edit_message_html(context.bot, msg.chat_id, status.message_id, error_msg(f"Bypass failed! Credit refunded.\nReason: {err_reason}"), reply_markup=result_kb())
        return

    u = get_user(user.id)
    result_text = (
        f"✅  <b>{b('Bypass Successful')}</b>  ✅\n\n"
        f"<b>• Original Link =</b> {H(query)}\n"
        f"<b>• Bypassed Link =</b> {bypassed_url}\n\n"
        f"💎 <b>{b('Credits Left')}</b> : <b>{u.get('credits', 0)}</b>{owner_footer()}"
    )

    await edit_message_html(context.bot, msg.chat_id, status.message_id, result_text, reply_markup=result_kb(), disable_web_page_preview=True)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text: return
    user = msg.from_user
    text = msg.text.strip()

    if user.id == ADMIN_ID:
        handled = await handle_admin_text(update, context)
        if handled: return

    if text.startswith("/"):
        if text.startswith("/bypass"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                await do_bypass(update, context, parts[1].strip())
            else:
                await send_html(context.bot, msg.chat_id, f"⚠️ <b>{b('Usage')}</b>\n\n<code>/bypass https://link.com</code>")
        return

    url_match = re.search(r'(https?://[^\s]+)', text)
    if url_match:
        await do_bypass(update, context, url_match.group(1))
    else:
        await send_html(context.bot, msg.chat_id, f"⚠️ Bypassing ke liye koi valid HTTP/HTTPS link bhejiye.")

# ================== REDEEM & REFERRAL & ADMIN ==================
async def redeem_cmd(update, context):
    msg = update.message
    user = update.effective_user
    if not get_user(user.id): create_user(user.id, user.username or "", user.first_name or "")
    if user.id != ADMIN_ID and await get_missing_channels(context.bot, user.id):
        await send_html(context.bot, msg.chat_id, force_join_msg(), reply_markup=force_join_kb()); return
    if not context.args:
        await send_html(context.bot, msg.chat_id, f"🎟️ <b>{b('Redeem Code')}</b>\n\nUsage : <code>/redeem YOURCODE</code>"); return
    
    code = context.args[0].strip().upper()
    result = use_code(code, user.id)
    if result == "invalid": text = f"❌ <b>{b('Invalid Code')}</b>\n\nYe code exist nahi karta.{owner_footer()}"
    elif result == "already": text = f"⚠️ <b>{b('Already Used')}</b>\n\nTum ye code pehle use kar chuke ho.{owner_footer()}"
    elif result == "full": text = f"❌ <b>{b('Code Expired')}</b>\n\nIs code ke saare uses khatam.{owner_footer()}"
    else:
        u = get_user(user.id)
        text = (f"🎉  <b>{b('Code Redeemed!')}</b>  🎉\n\n"
                f"🎟️ <b>{b('Code')}</b> : <code>{H(code)}</code>\n"
                f"💰 <b>{b('Credits Added')}</b> : +{result}\n"
                f"💎 <b>{b('New Balance')}</b> : {u.get('credits', 0)}\n\nAb bot use karo!{owner_footer()}")
    await send_html(context.bot, msg.chat_id, text, reply_markup=result_kb())

async def refer_cmd(update, context):
    if not get_user(update.effective_user.id): create_user(update.effective_user.id, "", "")
    bot_info = await context.bot.get_me()
    await send_html(context.bot, update.message.chat_id, referral_msg(update.effective_user.id, bot_info.username), reply_markup=back_kb())

async def credits_cmd(update, context):
    if not get_user(update.effective_user.id): create_user(update.effective_user.id, "", "")
    await send_html(context.bot, update.message.chat_id, credits_msg(update.effective_user.id), reply_markup=back_kb())

async def admin_cmd(update, context):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        await send_html(context.bot, update.message.chat_id, f"❌ <b>{b('Access Denied')}</b>")
        return
    await send_html(context.bot, update.message.chat_id, f"👑  <b>{b('Admin Panel')}</b>  👑", reply_markup=admin_kb())

async def broadcast_cmd(update, context):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return
    m = " ".join(context.args)
    users = db_fetch("SELECT user_id FROM users")
    st = await send_html(context.bot, update.message.chat_id, f"📢 Broadcasting to {len(users)}...")
    sent = fail = 0
    for u in users:
        try:
            await context.bot.send_message(u["user_id"], f"📢 <b>{b('Broadcast')}</b>\n\n{H(m)}", parse_mode=ParseMode.HTML)
            sent += 1
        except: fail += 1
        await asyncio.sleep(0.05)
    if st:
        try: await st.edit_text(f"✅ Sent: {sent}\n❌ Failed: {fail}")
        except: pass

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    d = q.data
    uid = q.from_user.id
    try: await q.answer()
    except: pass

    if d.startswith("a_"):
        if uid != ADMIN_ID: return
        await handle_admin_callback(q, context, d); return

    if not get_user(uid): create_user(uid, q.from_user.username or "", q.from_user.first_name or "")

    if d == "check_join_now":
        if await get_missing_channels(context.bot, uid):
            await edit_q(q, force_join_msg(), reply_markup=force_join_kb())
            try: await q.answer("Pehle channel join karo!", show_alert=True)
            except: pass
        else:
            mark_join_verified(uid)
            await edit_q(q, f"✅  <b>{b('Verified!')}</b>  ✅\n\nAb bot use kar sakte ho.\n\nNeeche se start karo 👇", reply_markup=main_menu_kb())
        return

    if uid != ADMIN_ID and d != "main_menu":
        if await get_missing_channels(context.bot, uid):
            await edit_q(q, force_join_msg(), reply_markup=force_join_kb()); return

    if d == "main_menu": await edit_q(q, welcome_msg(uid), reply_markup=main_menu_kb(), disable_web_page_preview=True)
    elif d == "menu_help": await edit_q(q, help_msg(), reply_markup=back_kb())
    elif d == "my_credits": await edit_q(q, credits_msg(uid), reply_markup=back_kb())
    elif d == "my_referral":
        bot_info = await context.bot.get_me()
        await edit_q(q, referral_msg(uid, bot_info.username), reply_markup=back_kb())
    elif d == "redeem_prompt": await edit_q(q, f"🎟️ <b>{b('Redeem Code')}</b>\n\nBhejo : <code>/redeem YOURCODE</code>", reply_markup=back_kb())
    elif d == "close_menu": await edit_q(q, f"❌ <b>{b('Menu Closed')}</b>")
    elif d == "new_lookup": await edit_q(q, f"🔍 <b>{b('New Bypass')}</b>\n\nBas koi short link message me bhejo!", reply_markup=back_kb())

async def handle_admin_callback(q, context, d):
    if d == "a_stats":
        users = total_users(); chs = len(get_admin_channels()) + len(REQUIRED_CHANNELS); codes = len(list_codes())
        h, r = divmod(int(time.time() - START_TIME), 3600); m, s = divmod(r, 60)
        text = (f"📊  <b>{b('Bot Statistics')}</b>  📊\n\n👥 <b>{b('Users')}</b> : {users}\n📢 <b>{b('Channels')}</b> : {chs}\n"
                f"🎟️ <b>{b('Codes')}</b> : {codes}\n⏱️ <b>{b('Uptime')}</b> : {h}h {m}m {s}s\n\n💎 <b>{b('Credit Economy')}</b> :\n"
                f"  Start : {CREDIT_START}\n  Ref : +{REFERRAL_REWARD}\n  Cost : {CREDIT_PER_LOOKUP}{owner_footer()}")
        await edit_q(q, text, reply_markup=admin_kb())
    elif d == "a_channels": await edit_q(q, "📢  <b>Force Join Channels</b>", reply_markup=channels_kb())
    elif d == "a_ch_add":
        context.user_data["awaiting"] = "ch_add"
        await edit_q(q, f"➕ <b>{b('Add Channel')}</b>\n\nBhejo : <code>@username Title</code>\n\nYa /cancel")
    elif d == "a_ch_remove":
        context.user_data["awaiting"] = "ch_remove"
        await edit_q(q, f"➖ <b>{b('Remove Channel')}</b>\n\nBhejo : <code>@username</code>\n\nYa /cancel")
    elif d == "a_ch_list":
        chs = get_admin_channels()
        txt = f"📢 <b>{b('Admin Channels')}</b>\n\n" + "".join([f"  @{H(c['username'])} — {H(c['title'])}\n" for c in chs]) if chs else "📢 No extra channels."
        await edit_q(q, txt, reply_markup=channels_kb())
    elif d == "a_back": await edit_q(q, f"👑  <b>{b('Admin Panel')}</b>  👑", reply_markup=admin_kb())
    elif d == "a_code_create":
        context.user_data["awaiting"] = "code_create"
        await edit_q(q, f"🎟️ <b>{b('Create Code')}</b>\n\nBhejo : <code>CODE CREDITS USES</code>\n\nYa /cancel")
    elif d == "a_code_list":
        codes = list_codes()
        txt = f"🎟️  <b>{b('Redeem Codes')}</b>  🎟️\n\n" + "".join([f"  <code>{H(c['code'])}</code> (💰 {c['credits']} | 📊 {c['used_count']}/{c['max_uses']})\n" for c in codes[:30]]) if codes else "🎟️ No codes."
        await edit_q(q, txt, reply_markup=admin_kb())
    elif d == "a_code_del":
        context.user_data["awaiting"] = "code_del"
        await edit_q(q, f"🗑️ <b>{b('Delete Code')}</b>\n\nBhejo : <code>CODE</code>\n\nYa /cancel")
    elif d == "a_broadcast": await edit_q(q, f"📣 <b>{b('Broadcast')}</b>\n\nCommand : <code>/broadcast message</code>")
    elif d == "a_close": await edit_q(q, f"❌ <b>{b('Admin Panel Closed')}</b>")

async def handle_admin_text(update, context):
    if update.effective_user.id != ADMIN_ID: return False
    awaiting = context.user_data.get("awaiting")
    if not awaiting: return False
    text = (update.message.text or "").strip()
    if text == "/cancel":
        context.user_data.pop("awaiting", None)
        await send_html(context.bot, update.message.chat_id, "✅ Cancelled.")
        return True
    if text.startswith("/"): return False

    if awaiting == "ch_add":
        parts = text.split(maxsplit=1)
        add_channel(parts[0].lstrip("@"), parts[1] if len(parts) > 1 else parts[0].lstrip("@"))
        context.user_data.pop("awaiting", None)
        await send_html(context.bot, update.message.chat_id, f"✅ Channel Added", reply_markup=admin_kb())
        return True
    if awaiting == "ch_remove":
        remove_channel(text.lstrip("@"))
        context.user_data.pop("awaiting", None)
        await send_html(context.bot, update.message.chat_id, f"✅ Channel Removed", reply_markup=admin_kb())
        return True
    if awaiting == "code_create":
        parts = text.split()
        if len(parts) >= 3:
            create_code(parts[0].upper(), int(parts[1]), int(parts[2]), update.effective_user.id)
            await send_html(context.bot, update.message.chat_id, f"✅ Code Created", reply_markup=admin_kb())
        context.user_data.pop("awaiting", None)
        return True
    if awaiting == "code_del":
        db_exec("DELETE FROM redeem_codes WHERE code=?", (text.upper(),))
        context.user_data.pop("awaiting", None)
        await send_html(context.bot, update.message.chat_id, f"✅ Code Deleted", reply_markup=admin_kb())
        return True
    return False

# ================== MAIN ==================
def main():
    print("=" * 60)
    print("🚀 Leon Bypass Bot starting...")
    print(f"Admin ID: {ADMIN_ID}")
    print("=" * 60)
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", lambda u, c: send_html(c.bot, u.message.chat_id, help_msg(), reply_markup=back_kb())))
    app.add_handler(CommandHandler("bypass", lambda u, c: do_bypass(u, c, u.message.text.split(maxsplit=1)[1]) if len(u.message.text.split()) > 1 else send_html(c.bot, u.message.chat_id, "Usage: /bypass <link>")))
    app.add_handler(CommandHandler("redeem", redeem_cmd))
    app.add_handler(CommandHandler("refer", refer_cmd))
    app.add_handler(CommandHandler("credits", credits_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot live!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
