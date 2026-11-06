# ============================================================
#  🚀 Leon Link Bypass Bot — MULTI-USER TURBO EDITION
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
from requests.adapters import HTTPAdapter
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

# High-concurrency HTTP session (supports 100+ simultaneous requests)
HTTP_SESSION = requests.Session()
adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=2)
HTTP_SESSION.mount("https://", adapter)
HTTP_SESSION.mount("http://", adapter)
HTTP_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
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
    return s.replace("<", "‹").replace(">", "›")[:500]


def H_code(value):
    if value is None: return "—"
    s = str(value).strip()
    if not s or s.lower() in ("null", "none"): return "—"
    s = s.replace("<", "").replace(">", "").replace("&", "and")
    return html.escape(s, quote=False)[:200]


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
    (25, "⚡", "Initializing Bypass Engine", "Connecting to high-speed nodes..."),
    (55, "🛰️", "Bypassing Shortener", "Solving redirects & ad-gateways..."),
    (85, "🔍", "Extracting Hidden Link", "Verifying destination URL..."),
    (100, "✅", "Bypass Complete", "Rendering output..."),
]

def thinking_msg(step=0, query=""):
    idx = min(max(step, 0), len(ANIM_STEPS) - 1)
    pct, icon, stage, detail = ANIM_STEPS[idx]
    q_line = f"🔗 <b>{b('Target')}</b> : <code>{H_code(query)}</code>\n\n" if query else ""
    return (
        f"👽  <b>{b('Leon Bypass Scanner')}</b>  👽\n\n"
        f"{q_line}"
        f"{icon} <b>{b(stage)}...</b>\n"
        f"<i>{detail}</i>\n\n"
        f"<code>[{progress_bar(pct)}] {pct}%</code>\n\n"
        f"⏳ <b>{sc('Please wait')}...</b>"
    )


# ================== CONCURRENT-SAFE DATABASE ==================
def get_conn():
    conn = sqlite3.connect(DB_FILE, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn

def db_init():
    conn = get_conn()
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
    conn = get_conn()
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()

def db_fetch(sql, params=()):
    conn = get_conn()
    try:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(sql, params)
        rows = c.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

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
        db_exec("""INSERT INTO redeem_codes
                   (code, credits, max_uses, created_by, created_at)
                   VALUES (?,?,?,?,?)""",
                (code.upper(), credits, max_uses, created_by, int(time.time())))
        return True
    except: return False

def get_code(code): return db_one("SELECT * FROM redeem_codes WHERE code=?", (code.upper(),))

def use_code(code, uid):
    c = get_code(code)
    if not c: return "invalid"
    if c["used_count"] >= c["max_uses"]: return "full"
    used = db_one("SELECT * FROM code_usage WHERE code=? AND user_id=?", (code.upper(), uid))
    if used: return "already"
    db_exec("INSERT INTO code_usage (code, user_id, used_at) VALUES (?,?,?)",
            (code.upper(), uid, int(time.time())))
    db_exec("UPDATE redeem_codes SET used_count = used_count + 1 WHERE code=?", (code.upper(),))
    add_credits(uid, c["credits"])
    return c["credits"]

def delete_code(code):
    db_exec("DELETE FROM redeem_codes WHERE code=?", (code.upper(),))
    db_exec("DELETE FROM code_usage WHERE code=?", (code.upper(),))

def list_codes(): return db_fetch("SELECT * FROM redeem_codes ORDER BY created_at DESC")

def total_users():
    r = db_one("SELECT COUNT(*) as n FROM users")
    return r["n"] if r else 0

def mark_join_verified(uid):
    db_exec("INSERT OR REPLACE INTO join_verified (user_id, verified_at) VALUES (?, ?)",
            (uid, int(time.time())))


# ================== PARALLEL FORCE JOIN ==================
def all_required_channels():
    chs = list(REQUIRED_CHANNELS)
    existing = {c["username"].lower() for c in chs}
    for ac in get_admin_channels():
        un = ac["username"].lower().strip().lstrip("@")
        if un and un not in existing:
            chs.append({
                "username": un,
                "title": ac.get("title") or un,
                "url": f"https://t.me/{un}",
            })
            existing.add(un)
    return chs


async def _check_single_channel(bot, ch, uid):
    try:
        m = await bot.get_chat_member(chat_id=f"@{ch['username']}", user_id=uid)
        if m.status not in ("member", "administrator", "creator"):
            return ch
        return None
    except Exception as e:
        logger.warning(f"Channel check @{ch['username']} for {uid}: {e}")
        return ch


async def get_missing_channels(bot, uid):
    chs = all_required_channels()
    results = await asyncio.gather(*(_check_single_channel(bot, ch, uid) for ch in chs))
    return [r for r in results if r is not None]


def force_join_kb():
    rows = []
    for ch in all_required_channels():
        rows.append([InlineKeyboardButton(
            f"📢 Join {ch['title']}",
            url=ch["url"],
            style="primary"
        )])
    rows.append([InlineKeyboardButton(
        "✅ I Joined All",
        callback_data="check_join_now",
        style="success"
    )])
    return InlineKeyboardMarkup(rows)


def force_join_msg():
    ch_lines = "\n".join(f"  🔗 @{c['username']}" for c in all_required_channels())
    return (
        f"🔒  <b>{b('Join Required')}</b>  🔒\n\n"
        f"👋 Bot use karne se pehle\n"
        f"channel join karna zaroori hai\n\n"
        f"📢 <b>{b('Required Channel')}</b> :\n"
        f"{ch_lines}\n\n"
        f"👇 Neeche button se join karo\n"
        f"Phir ✅ <b>I Joined All</b> dabao"
    )


# ================== BUTTONS ==================
def btn(text, **kw):
    return InlineKeyboardButton(text, **kw)

def main_menu_kb():
    return InlineKeyboardMarkup([
        [btn("🔓 " + sc("Bypass Link"), callback_data="hlp_bypass", style="success"),
         btn("⚡ " + sc("Supported"), callback_data="hlp_supported", style="primary")],
        [btn("💎 " + sc("My Credits"), callback_data="my_credits", style="success"),
         btn("🎁 " + sc("Referral"), callback_data="my_referral", style="primary")],
        [btn("🎟️ " + sc("Redeem Code"), callback_data="redeem_prompt", style="success"),
         btn("📖 " + sc("Help"), callback_data="menu_help", style="primary")],
        [btn("👑 " + sc("Owner"), url=OWNER_LINK, style="primary"),
         btn("❌ " + sc("Close"), callback_data="close_menu", style="danger")],
    ])

def back_kb():
    return InlineKeyboardMarkup([
        [btn("⬅️ " + sc("Back"), callback_data="main_menu", style="primary")]])

def result_kb(bypassed_url=None):
    rows = []
    if bypassed_url and bypassed_url.startswith(("http://", "https://")):
        rows.append([btn("🌐 " + sc("Open Bypassed Link"), url=bypassed_url, style="success")])
    rows.append([
        btn("🔓 " + sc("New Bypass"), callback_data="new_lookup", style="success"),
        btn("🏠 " + sc("Menu"), callback_data="main_menu", style="primary")
    ])
    rows.append([btn("👑 " + sc("Owner"), url=OWNER_LINK, style="primary")])
    return InlineKeyboardMarkup(rows)

def admin_kb():
    return InlineKeyboardMarkup([
        [btn("📊 " + sc("Stats"), callback_data="a_stats", style="success"),
         btn("📢 " + sc("Channels"), callback_data="a_channels", style="primary")],
        [btn("🎟️ " + sc("Create Code"), callback_data="a_code_create", style="success"),
         btn("📋 " + sc("List Codes"), callback_data="a_code_list", style="primary")],
        [btn("🗑️ " + sc("Delete Code"), callback_data="a_code_del", style="danger"),
         btn("📣 " + sc("Broadcast"), callback_data="a_broadcast", style="primary")],
        [btn("❌ " + sc("Close"), callback_data="a_close", style="danger")]])

def channels_kb():
    return InlineKeyboardMarkup([
        [btn("➕ " + sc("Add Channel"), callback_data="a_ch_add", style="success"),
         btn("➖ " + sc("Remove Channel"), callback_data="a_ch_remove", style="danger")],
        [btn("📋 " + sc("List Channels"), callback_data="a_ch_list", style="primary"),
         btn("⬅️ " + sc("Back"), callback_data="a_back", style="primary")]])


def owner_footer():
    return (f"\n\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>{b('Owner')}</b> : {OWNER_USERNAME}\n"
            f"🤖 <b>{b('Bot')}</b> : @Leonbypassbot")


# ================== MESSAGES ==================
def welcome_msg(uid):
    u = get_user(uid) or {}
    return (
        f"👽  <b>{b('Leon Bypass Bot')}</b>  👽\n\n"
        f"👋 <b>{b('Namaste')}</b>, <b>{H(u.get('first_name') or 'Dost')}</b>!\n\n"
        f"Main ek advanced Shortener Bypass bot hoon.\n"
        f"Kisi bhi shortener link ke andar chupa hua\n"
        f"real destination link turant nikal sakta hoon.\n\n"
        f"💎 <b>{b('Credits')}</b> : <b>{u.get('credits', 0)}</b>\n"
        f"🎁 <b>{b('Referrals')}</b> : <b>{u.get('referral_count', 0)}</b>\n\n"
        f"✨ <b>{b('Features')}</b> :\n"
        f"  🔓 {sc('Instant Shortener Bypass')}\n"
        f"  ⚡ {sc('Auto Link Detection')}\n"
        f"  🛡️ {sc('Ad-Gateway Unlocker')}\n\n"
        f"👇 Seedha link bhejo ya neeche buttons use karo{owner_footer()}")


def help_msg():
    return (
        f"📖  <b>{b('Help Menu')}</b>  📖\n\n"
        f"🔓 <b>{b('DIRECT BYPASS')}</b>\n"
        f"Seedha chat me koi bhi shortener link bhejo!\n"
        f"Example : <code>https://shortxlinks.in/EqJlsCQt</code>\n\n"
        f"🔗 <b>{b('COMMAND BYPASS')}</b>\n"
        f"<code>/bypass https://softurl.in/cnqT</code>\n\n"
        f"🎟️ <b>{b('REDEEM')}</b> : <code>/redeem CODE</code>\n"
        f"🎁 <b>{b('REFERRAL')}</b> : <code>/refer</code>\n"
        f"💎 <b>{b('CREDITS')}</b> : <code>/credits</code>\n\n"
        f"💡 Seedha link paste karo, bot auto bypass kar dega!{owner_footer()}")


def credits_msg(uid):
    u = get_user(uid) or {}
    return (
        f"💎  <b>{b('My Credits')}</b>  💎\n\n"
        f"💎 <b>{b('Balance')}</b> : <b>{u.get('credits', 0)}</b>\n"
        f"📊 <b>{b('Total Bypass')}</b> : {u.get('total_lookups', 0)}\n"
        f"🎁 <b>{b('Referrals')}</b> : {u.get('referral_count', 0)}\n\n"
        f"Har bypass me 1 credit lagta hai.\n"
        f"Referral se 15 credits milte hain.{owner_footer()}")


def referral_msg(uid, bot_username):
    u = get_user(uid) or {}
    link = f"https://t.me/{bot_username}?start=ref_{uid}"
    return (
        f"🎁  <b>{b('Referral Program')}</b>  🎁\n\n"
        f"🔗 <b>{b('Your Link')}</b> :\n"
        f"<code>{H_code(link)}</code>\n\n"
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


# ================== API & PARSER ==================
def norm_url(u):
    if not u: return ""
    return re.sub(r"^https?://(www\.)?", "", str(u).strip(), flags=re.IGNORECASE).rstrip("/").lower()


def extract_bypass_result(data, original_query):
    if not data:
        return None

    orig_norm = norm_url(original_query)
    all_texts = []

    def walk(obj):
        if obj is None:
            return
        if isinstance(obj, str):
            all_texts.append(obj)
        elif isinstance(obj, dict):
            priority_keys = (
                "bypassed", "bypassed_url", "bypassed_link", "destination",
                "destination_url", "final_url", "final_link", "direct_url",
                "direct_link", "target_url", "target", "real_url", "resolved_url",
                "unlocked_url", "output", "result", "data", "response", "url", "link"
            )
            seen = set()
            for pk in priority_keys:
                for k, v in obj.items():
                    if k.lower() == pk and k not in seen:
                        seen.add(k)
                        walk(v)
            for k, v in obj.items():
                if k not in seen:
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
        else:
            all_texts.append(str(obj))

    walk(data)
    combined_text = "\n".join(all_texts)

    label_patterns = [
        r"(?:BYPASSED|DESTINATION|FINAL|DIRECT|REAL|TARGET|UNLOCKED|RESOLVED|DECRYPTED|EXTRACTED|OUTPUT)\s*(?:LINK|URL|DESTINATION|ADDRESS)?\s*[:=\-]+\s*(https?://[^\s<>\"'\)\]]+)",
        r"(?:BYPASSED|DESTINATION|FINAL|DIRECT|REAL|TARGET|UNLOCKED|RESOLVED)\s*[:=\-]+\s*(https?://[^\s<>\"'\)\]]+)",
        r"(?:BYPASSED|DESTINATION|FINAL|DIRECT|REAL|TARGET)\s*(?:LINK|URL)?\s*[:=\-]+\s*((?:t\.me|telegram\.me|mega\.nz|drive\.google\.com)/[^\s<>\"'\)\]]+)",
    ]
    for pat in label_patterns:
        matches = re.findall(pat, combined_text, flags=re.IGNORECASE)
        for m in matches:
            candidate = m.strip().rstrip(".,;)")
            if not candidate.startswith(("http://", "https://")):
                candidate = "https://" + candidate
            if norm_url(candidate) != orig_norm and "altaf-api-maker" not in candidate.lower():
                return candidate

    all_urls = re.findall(r"(https?://[^\s<>\"'\)\]]+)", combined_text)
    non_orig_urls = []
    for u in all_urls:
        clean_u = u.strip().rstrip(".,;)")
        if "altaf-api-maker.base44.app" in clean_u.lower():
            continue
        if norm_url(clean_u) != orig_norm:
            non_orig_urls.append(clean_u)

    if non_orig_urls:
        return non_orig_urls[-1]

    tg_links = re.findall(r"\b((?:t\.me|telegram\.me|telegram\.dog)/[A-Za-z0-9_/\+\-\?=&]+)", combined_text, flags=re.IGNORECASE)
    for tl in tg_links:
        full_tl = "https://" + tl.strip().rstrip(".,;)")
        if norm_url(full_tl) != orig_norm:
            return full_tl

    return None


def api_call(query):
    clean_q = str(query).strip()
    url = f"{API_BASE}{quote(clean_q, safe='')}"
    try:
        r = HTTP_SESSION.get(url, timeout=30)
        if r.status_code in (200, 201):
            try:
                parsed = r.json()
            except Exception:
                parsed = r.text
            if parsed:
                bypassed = extract_bypass_result(parsed, clean_q)
                if bypassed:
                    return {"bypassed_url": bypassed, "raw": parsed}
    except Exception as e:
        logger.warning(f"API attempt error: {e}")
    return None


# ================== SAFE SEND/EDIT ==================
def plain_strip(text):
    return re.sub(r"<[^>]+>", "", str(text))

async def send_html(bot, chat_id, text, **kwargs):
    try:
        return await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML, **kwargs)
    except Exception as e:
        logger.warning(f"HTML send failed: {e}")
        try:
            return await bot.send_message(chat_id, plain_strip(text), **kwargs)
        except Exception as e2:
            logger.error(f"Plain send failed: {e2}")
            return None

async def edit_q(q, text, **kwargs):
    try:
        return await q.edit_message_text(text=text, parse_mode=ParseMode.HTML, **kwargs)
    except Exception as e:
        logger.warning(f"q.edit failed: {e}")
        try:
            return await q.edit_message_text(text=plain_strip(text), **kwargs)
        except Exception as e2:
            logger.error(f"q plain edit failed: {e2}")
            return None

async def edit_message_html(bot, chat_id, message_id, text, **kwargs):
    try:
        return await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                            text=text, parse_mode=ParseMode.HTML, **kwargs)
    except Exception as e:
        logger.warning(f"HTML edit failed: {e}")
        try:
            return await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                text=plain_strip(text), **kwargs)
        except Exception as e2:
            logger.error(f"Plain edit failed: {e2}")
            return None


# ================== /start ==================
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
                await context.bot.send_message(referred_by,
                    f"🎁 <b>{b('New Referral!')}</b>\n\n"
                    f"👤 {H(user.first_name)} ne tumhara link use kiya\n"
                    f"💰 Tumhe <b>+{REFERRAL_REWARD}</b> credits mile! 🎉",
                    parse_mode=ParseMode.HTML)
            except: pass
    else:
        db_exec("UPDATE users SET last_seen=?, username=?, first_name=? WHERE user_id=?",
                (int(time.time()), user.username or "", user.first_name or "", user.id))

    if user.id != ADMIN_ID:
        missing = await get_missing_channels(context.bot, user.id)
        if missing:
            await send_html(context.bot, msg.chat_id, force_join_msg(),
                             reply_markup=force_join_kb())
            return

    if is_new:
        u = get_user(user.id)
        text = (f"🎉  <b>{b('Welcome!')}</b>  🎉\n\n"
                f"👋 <b>{b('Namaste')}</b> {H(user.first_name)}!\n\n"
                f"✅ <b>{b('Account created!')}</b>\n\n"
                f"💎 <b>{b('Starting Credits')}</b> : {CREDIT_START}\n")
        if referred_by:
            text += f"🎁 <b>{b('Referral Bonus')}</b> : +{REFERRAL_BONUS_NEW}\n"
        text += (f"\n🎯 <b>{b('Total Credits')}</b> : {u.get('credits', CREDIT_START)}\n\n"
                 f"Ab koi bhi shortener link bhejo!{owner_footer()}")
        await send_html(context.bot, msg.chat_id, text, reply_markup=main_menu_kb(),
                         disable_web_page_preview=True)
    else:
        await send_html(context.bot, msg.chat_id, welcome_msg(user.id),
                         reply_markup=main_menu_kb(), disable_web_page_preview=True)


# ================== NON-BLOCKING BYPASS HANDLER ==================
async def bypass_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await send_html(context.bot, update.message.chat_id,
                         f"⚠️ <b>{b('Usage')}</b>\n\n<code>/bypass https://shortxlinks.in/EqJlsCQt</code>")
        return
    query = " ".join(context.args).strip()
    await do_bypass(update, context, query)


async def do_bypass(update, context, query):
    msg = update.message
    user = update.effective_user

    if not get_user(user.id):
        create_user(user.id, user.username or "", user.first_name or "")

    if user.id != ADMIN_ID:
        missing = await get_missing_channels(context.bot, user.id)
        if missing:
            await send_html(context.bot, msg.chat_id, force_join_msg(),
                             reply_markup=force_join_kb())
            return

    if not use_credits(user.id, CREDIT_PER_LOOKUP):
        await send_html(context.bot, msg.chat_id, no_credits_msg())
        return

    inc_lookup(user.id)

    status = await send_html(context.bot, msg.chat_id, thinking_msg(0, query), disable_web_page_preview=True)
    if not status: return

    api_task = asyncio.create_task(asyncio.to_thread(api_call, query))

    current_step = 1
    while not api_task.done() and current_step < len(ANIM_STEPS) - 1:
        await asyncio.sleep(0.6)
        if not api_task.done():
            try:
                await status.edit_text(thinking_msg(current_step, query),
                                       parse_mode=ParseMode.HTML,
                                       disable_web_page_preview=True)
            except:
                pass
            current_step += 1

    res = None
    try:
        res = await api_task
    except Exception as e:
        logger.error(f"API task error: {e}")

    if not res or not res.get("bypassed_url"):
        add_credits(user.id, CREDIT_PER_LOOKUP)
        await edit_message_html(
            context.bot, msg.chat_id, status.message_id,
            error_msg("Is link ko bypass nahi kiya ja saka. Credit refunded."),
            reply_markup=result_kb()
        )
        return

    bypassed_url = res["bypassed_url"]
    u = get_user(user.id) or {}
    credits = u.get("credits", 0)

    result_text = (
        f"🔓  <b>{b('Bypass Result')}</b>  🔓\n\n"
        f"🎯 <b>{b('Query')}</b> : <code>{H_code(query)}</code>\n\n"
        f"<b>• Short Link = {H(query)}</b>\n"
        f"<b>• Bypassed Link = {H(bypassed_url)}</b>\n\n"
        f"💎 <b>{b('Credits Left')}</b> : <b>{credits}</b>{owner_footer()}"
    )

    await edit_message_html(
        context.bot, msg.chat_id, status.message_id, result_text,
        reply_markup=result_kb(bypassed_url),
        disable_web_page_preview=True
    )


# ================== REDEEM / REFER / CREDITS ==================
async def redeem_cmd(update, context):
    msg = update.message
    user = update.effective_user
    if not get_user(user.id):
        create_user(user.id, user.username or "", user.first_name or "")

    if user.id != ADMIN_ID:
        missing = await get_missing_channels(context.bot, user.id)
        if missing:
            await send_html(context.bot, msg.chat_id, force_join_msg(),
                             reply_markup=force_join_kb())
            return

    if not context.args:
        await send_html(context.bot, msg.chat_id,
                         f"🎟️ <b>{b('Redeem Code')}</b>\n\nUsage : <code>/redeem YOURCODE</code>")
        return

    code = context.args[0].strip().upper()
    result = use_code(code, user.id)
    if result == "invalid":
        text = f"❌ <b>{b('Invalid Code')}</b>\n\nYe code exist nahi karta.{owner_footer()}"
    elif result == "already":
        text = f"⚠️ <b>{b('Already Used')}</b>\n\nTum ye code pehle use kar chuke ho.{owner_footer()}"
    elif result == "full":
        text = f"❌ <b>{b('Code Expired')}</b>\n\nIs code ke saare uses khatam.{owner_footer()}"
    else:
        u = get_user(user.id)
        text = (f"🎉  <b>{b('Code Redeemed!')}</b>  🎉\n\n"
                f"🎟️ <b>{b('Code')}</b> : <code>{H_code(code)}</code>\n"
                f"💰 <b>{b('Credits Added')}</b> : +{result}\n"
                f"💎 <b>{b('New Balance')}</b> : {u.get('credits', 0)}\n\n"
                f"Ab bot use karo!{owner_footer()}")

    await send_html(context.bot, msg.chat_id, text, reply_markup=result_kb())


async def refer_cmd(update, context):
    msg = update.message
    user = update.effective_user
    if not get_user(user.id):
        create_user(user.id, user.username or "", user.first_name or "")
    if user.id != ADMIN_ID:
        missing = await get_missing_channels(context.bot, user.id)
        if missing:
            await send_html(context.bot, msg.chat_id, force_join_msg(), reply_markup=force_join_kb())
            return
    bot_info = await context.bot.get_me()
    await send_html(context.bot, msg.chat_id, referral_msg(user.id, bot_info.username),
                     reply_markup=back_kb())


async def credits_cmd(update, context):
    msg = update.message
    user = update.effective_user
    if not get_user(user.id):
        create_user(user.id, user.username or "", user.first_name or "")
    if user.id != ADMIN_ID:
        missing = await get_missing_channels(context.bot, user.id)
        if missing:
            await send_html(context.bot, msg.chat_id, force_join_msg(), reply_markup=force_join_kb())
            return
    await send_html(context.bot, msg.chat_id, credits_msg(user.id),
                     reply_markup=back_kb())


# ================== ADMIN ==================
async def admin_cmd(update, context):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        await send_html(context.bot, update.message.chat_id,
                         f"❌ <b>{b('Access Denied')}</b>\n\nTum admin nahi ho.")
        return
    await send_html(context.bot, update.message.chat_id,
                     f"👑  <b>{b('Admin Panel')}</b>  👑\n\nSelect option below:",
                     reply_markup=admin_kb())


async def broadcast_cmd(update, context):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await send_html(context.bot, update.message.chat_id, "Usage: /broadcast <message>")
        return
    m = " ".join(context.args)
    users = db_fetch("SELECT user_id FROM users")
    sent = fail = 0
    st = await send_html(context.bot, update.message.chat_id,
                          f"📢 Broadcasting to {len(users)}...")
    for idx, u in enumerate(users):
        try:
            await context.bot.send_message(u["user_id"],
                                            f"📢 <b>{b('Broadcast')}</b>\n\n{H(m)}",
                                            parse_mode=ParseMode.HTML)
            sent += 1
        except: fail += 1
        if (idx + 1) % 10 == 0 and st:
            try: await st.edit_text(f"📢 {idx+1}/{len(users)}")
            except: pass
        await asyncio.sleep(0.05)
    if st:
        try: await st.edit_text(f"✅ Sent: {sent}\n❌ Failed: {fail}")
        except: pass


# ================== CALLBACK HANDLER ==================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    d = q.data
    uid = q.from_user.id
    try: await q.answer()
    except: pass

    if d.startswith("a_"):
        if uid != ADMIN_ID:
            try: await q.answer("Access denied.", show_alert=True)
            except: pass
            return
        await handle_admin_callback(q, context, d)
        return

    if not get_user(uid):
        create_user(uid, q.from_user.username or "", q.from_user.first_name or "")

    if d == "check_join_now":
        missing = await get_missing_channels(context.bot, uid)
        if missing:
            await edit_q(q, force_join_msg(), reply_markup=force_join_kb())
            try: await q.answer("❌ Pehle @sterniterspro join karo!", show_alert=True)
            except: pass
        else:
            mark_join_verified(uid)
            await edit_q(q,
                f"✅  <b>{b('Verified!')}</b>  ✅\n\n"
                f"Ab bot use kar sakte ho.\n\nNeeche se start karo 👇",
                reply_markup=main_menu_kb())
        return

    if uid != ADMIN_ID:
        missing = await get_missing_channels(context.bot, uid)
        if missing:
            await edit_q(q, force_join_msg(), reply_markup=force_join_kb())
            return

    if d == "main_menu":
        await edit_q(q, welcome_msg(uid), reply_markup=main_menu_kb(),
                      disable_web_page_preview=True)
    elif d == "menu_help":
        await edit_q(q, help_msg(), reply_markup=back_kb())
    elif d == "my_credits":
        await edit_q(q, credits_msg(uid), reply_markup=back_kb())
    elif d == "my_referral":
        bot_info = await context.bot.get_me()
        await edit_q(q, referral_msg(uid, bot_info.username), reply_markup=back_kb())
    elif d == "redeem_prompt":
        await edit_q(q, f"🎟️ <b>{b('Redeem Code')}</b>\n\nBhejo : <code>/redeem YOURCODE</code>",
                      reply_markup=back_kb())
    elif d == "close_menu":
        await edit_q(q, f"❌ <b>{b('Menu Closed')}</b>")
    elif d in ("new_lookup", "hlp_bypass"):
        await edit_q(q,
            f"🔓 <b>{b('Bypass Shortener Link')}</b>\n\n"
            f"Seedha chat me apna short link bhejo:\n"
            f"<code>https://shortxlinks.in/EqJlsCQt</code>\n\n"
            f"💰 Cost : {CREDIT_PER_LOOKUP} credit",
            reply_markup=back_kb())
    elif d == "hlp_supported":
        await edit_q(q,
            f"⚡ <b>{b('Supported Shorteners')}</b>\n\n"
            f"• Shortxlinks, Softurl, GPLinks, Droplink\n"
            f"• Adrinolinks, VPLink, ShrinkMe, Linkvertise\n"
            f"• Earn4Link, TNShort, V2Links & 100+ more!\n\n"
            f"💡 Seedha link bhejo aur instant bypass pao!",
            reply_markup=back_kb())


async def handle_admin_callback(q, context, d):
    if d == "a_stats":
        users = total_users()
        chs = len(all_required_channels())
        codes = len(list_codes())
        up = int(time.time() - START_TIME)
        h, r = divmod(up, 3600); m, s = divmod(r, 60)
        text = (f"📊  <b>{b('Bot Statistics')}</b>  📊\n\n"
                f"👥 <b>{b('Users')}</b> : {users}\n"
                f"📢 <b>{b('Channels')}</b> : {chs}\n"
                f"🎟️ <b>{b('Active Codes')}</b> : {codes}\n"
                f"⏱️ <b>{b('Uptime')}</b> : {h}h {m}m {s}s\n\n"
                f"💎 <b>{b('Credit Economy')}</b> :\n"
                f"  Start : {CREDIT_START}\n"
                f"  Referrer : +{REFERRAL_REWARD}\n"
                f"  Referred : +{REFERRAL_BONUS_NEW}\n"
                f"  Cost : {CREDIT_PER_LOOKUP}{owner_footer()}")
        await edit_q(q, text, reply_markup=admin_kb())
    elif d == "a_channels":
        chs_admin = get_admin_channels()
        txt = f"📢  <b>{b('Force Join Channels')}</b>  📢\n\n"
        txt += f"<b>🔒 Default (Locked)</b> :\n"
        for c in REQUIRED_CHANNELS:
            txt += f"  @{H_code(c['username'])} — {H(c['title'])}\n"
        txt += f"\n<b>➕ Admin Added</b> :\n"
        if chs_admin:
            for c in chs_admin:
                txt += f"  @{H_code(c['username'])} — {H(c.get('title') or 'N/A')}\n"
        else:
            txt += f"  None\n"
        txt += f"\nChoose action:"
        await edit_q(q, txt, reply_markup=channels_kb())
    elif d == "a_ch_add":
        context.user_data["awaiting"] = "ch_add"
        await edit_q(q, f"➕ <b>{b('Add Channel')}</b>\n\n"
                        f"Bhejo : <code>@username Title</code>\n\n"
                        f"Example:\n<code>@mychannel My Channel</code>\n\nYa /cancel")
    elif d == "a_ch_remove":
        context.user_data["awaiting"] = "ch_remove"
        await edit_q(q, f"➖ <b>{b('Remove Channel')}</b>\n\n"
                        f"Bhejo : <code>@username</code>\n\n"
                        f"⚠️ Default channel remove nahi hoga.\n\nYa /cancel")
    elif d == "a_ch_list":
        chs = get_admin_channels()
        if not chs:
            await edit_q(q, f"📢 No extra channels.", reply_markup=channels_kb())
        else:
            txt = f"📢 <b>{b('Admin Channels')}</b>\n\n"
            for c in chs:
                txt += f"  @{H_code(c['username'])} — {H(c.get('title') or 'N/A')}\n"
            await edit_q(q, txt, reply_markup=channels_kb())
    elif d == "a_back":
        await edit_q(q, f"👑  <b>{b('Admin Panel')}</b>  👑\n\nSelect option:",
                      reply_markup=admin_kb())
    elif d == "a_code_create":
        context.user_data["awaiting"] = "code_create"
        await edit_q(q, f"🎟️ <b>{b('Create Code')}</b>\n\n"
                        f"Bhejo : <code>CODE CREDITS USES</code>\n\n"
                        f"Example:\n<code>LEON50 50 10</code>\n\nYa /cancel")
    elif d == "a_code_list":
        codes = list_codes()
        if not codes:
            await edit_q(q, f"🎟️ No codes.", reply_markup=admin_kb())
            return
        txt = f"🎟️  <b>{b('Redeem Codes')}</b>  🎟️\n\n"
        for c in codes[:30]:
            txt += (f"  <code>{H_code(c['code'])}</code>\n"
                    f"     💰 {c['credits']} | 📊 {c['used_count']}/{c['max_uses']}\n")
        await edit_q(q, txt, reply_markup=admin_kb())
    elif d == "a_code_del":
        context.user_data["awaiting"] = "code_del"
        await edit_q(q, f"🗑️ <b>{b('Delete Code')}</b>\n\n"
                        f"Bhejo : <code>CODE</code>\n\nYa /cancel")
    elif d == "a_broadcast":
        await edit_q(q, f"📣 <b>{b('Broadcast')}</b>\n\n"
                        f"Command : <code>/broadcast Your message</code>")
    elif d == "a_close":
        await edit_q(q, f"❌ <b>{b('Admin Panel Closed')}</b>")


# ================== ADMIN TEXT ==================
async def handle_admin_text(update, context):
    if update.effective_user.id != ADMIN_ID: return False
    awaiting = context.user_data.get("awaiting")
    if not awaiting: return False

    text = (update.message.text or "").strip()
    if text == "/cancel":
        context.user_data.pop("awaiting", None)
        await send_html(context.bot, update.message.chat_id, "✅ Cancelled.")
        return True
    if not text or text.startswith("/"): return False

    if awaiting == "ch_add":
        parts = text.split(maxsplit=1)
        uname = parts[0].lstrip("@")
        title = parts[1] if len(parts) > 1 else uname
        add_channel(uname, title)
        context.user_data.pop("awaiting", None)
        await send_html(context.bot, update.message.chat_id,
                         f"✅ <b>{b('Channel Added')}</b>\n\n  @{H(uname)} — {H(title)}",
                         reply_markup=admin_kb())
        return True
    if awaiting == "ch_remove":
        uname = text.lstrip("@")
        remove_channel(uname)
        context.user_data.pop("awaiting", None)
        await send_html(context.bot, update.message.chat_id,
                         f"✅ <b>{b('Channel Removed')}</b>\n\n  @{H(uname)}",
                         reply_markup=admin_kb())
        return True
    if awaiting == "code_create":
        parts = text.split()
        if len(parts) < 3:
            await send_html(context.bot, update.message.chat_id, "Format: CODE CREDITS USES")
            return True
        try:
            code = parts[0].upper(); credits = int(parts[1]); uses = int(parts[2])
        except:
            await send_html(context.bot, update.message.chat_id, "Invalid numbers.")
            return True
        if create_code(code, credits, uses, update.effective_user.id):
            await send_html(context.bot, update.message.chat_id,
                             f"✅ <b>{b('Code Created')}</b>\n\n"
                             f"🎟️ <code>{H_code(code)}</code>\n💰 {credits}\n📊 {uses}",
                             reply_markup=admin_kb())
        else:
            await send_html(context.bot, update.message.chat_id, "❌ Code already exists.")
        context.user_data.pop("awaiting", None)
        return True
    if awaiting == "code_del":
        delete_code(text.upper())
        context.user_data.pop("awaiting", None)
        await send_html(context.bot, update.message.chat_id,
                         f"✅ <b>{b('Code Deleted')}</b>\n\n  <code>{H_code(text.upper())}</code>",
                         reply_markup=admin_kb())
        return True
    return False


# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text: return
    user = msg.from_user
    text = msg.text.strip()
    if text.startswith("/"): return

    if user.id == ADMIN_ID:
        handled = await handle_admin_text(update, context)
        if handled: return

    if not get_user(user.id):
        create_user(user.id, user.username or "", user.first_name or "")

    if user.id != ADMIN_ID:
        missing = await get_missing_channels(context.bot, user.id)
        if missing:
            await send_html(context.bot, msg.chat_id, force_join_msg(),
                             reply_markup=force_join_kb())
            return

    url_match = re.search(r"(https?://[^\s<>\"']+)", text)
    if url_match:
        await do_bypass(update, context, url_match.group(1).strip())
        return

    domain_match = re.search(r"\b([a-zA-Z0-9\-]+\.[a-zA-Z]{2,}/[^\s<>\"']+)", text)
    if domain_match:
        await do_bypass(update, context, "https://" + domain_match.group(1).strip())
        return

    await send_html(
        context.bot, msg.chat_id,
        f"⚠️ <b>{b('Invalid Input')}</b>\n\n"
        f"Koi valid shortener link bhejo!\n"
        f"Example : <code>https://shortxlinks.in/EqJlsCQt</code>",
        reply_markup=main_menu_kb()
    )


# ================== MAIN (MULTI-USER CONCURRENT) ==================
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing.")
    print("=" * 60)
    print("👽 Leon Bypass Bot starting (Multi-User Concurrent Mode)...")
    print(f"Admin ID: {ADMIN_ID}")
    print("=" * 60)

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .connection_pool_size(128)
        .pool_timeout(30.0)
        .connect_timeout(20.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", lambda u, c: send_html(c.bot, u.message.chat_id, help_msg(), reply_markup=back_kb())))
    app.add_handler(CommandHandler("bypass", bypass_cmd))
    app.add_handler(CommandHandler("redeem", redeem_cmd))
    app.add_handler(CommandHandler("refer", refer_cmd))
    app.add_handler(CommandHandler("credits", credits_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot live (Concurrent Multi-User Active)!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
