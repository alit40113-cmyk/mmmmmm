# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـمـحـدودة والـشـامـلـة
# 🛡️ نـظـام الـتـنـصـيـب والـحـماية مـع تـحـديـد عـدد الـمـشـتـركـين
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os
import sys
import time
import json
import sqlite3
import logging
import hashlib
import secrets
import requests
import threading
import subprocess
import platform
import psutil
import re
import tempfile
import shutil
from io import BytesIO
from datetime import datetime, timedelta
from collections import defaultdict
import telebot
from telebot import types

# ----------------------------------------------------------
# 🔑 إعـدادات الـنـظـام الـمـركـزيـة
# ----------------------------------------------------------

BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'

# ⚠️ تحديد عدد المستخدمين المسموح لهم باستخدام البوت
MAX_USERS_LIMIT = 50  # يمكنك تغيير الرقم حسب رغبتك

DB_PATH = 'titan_v37_limited.db'
UPLOAD_FOLDER = 'hosted_bots_data'
LOG_FILE = 'titan_system.log'

# إعداد السجلات البرمجية
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("Titan-V37")

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------------
# 🗄️ تـهـيـئـة قـاعـدة الـبـيـانـات الـعـمـلاقـة
# ----------------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        points INTEGER DEFAULT 10, 
        join_date TEXT, 
        is_banned INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS active_bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        bot_name TEXT, 
        process_id INTEGER, 
        expiry_time TEXT, 
        status TEXT DEFAULT 'running'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS installation_requests (
        req_id TEXT PRIMARY KEY, 
        user_id INTEGER, 
        file_id TEXT, 
        file_name TEXT, 
        upload_time TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS gift_codes (
        code TEXT PRIMARY KEY, 
        points INTEGER, 
        max_uses INTEGER, 
        current_uses INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS used_codes (
        user_id INTEGER, 
        code TEXT,
        use_time TEXT
    )''')
    conn.commit()
    conn.close()

setup_database()

# ----------------------------------------------------------
# 🛡️ مـحـرك الـتـحـقـق والـحـمـايـة (نـظـام الـعـدد الـمـحـدود)
# ----------------------------------------------------------

def get_users_count():
    conn = get_db_connection()
    count = conn.execute('SELECT count(*) FROM users').fetchone()[0]
    conn.close()
    return count

def verify_user_access(uid, username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    
    if user:
        conn.close()
        return True, "welcome"
    
    # إذا لم يكن مسجلاً، نتحقق من العدد الحالي
    current_count = get_users_count()
    if current_count >= MAX_USERS_LIMIT:
        conn.close()
        return False, "limit_reached"
    
    # تسجيل المستخدم الجديد
    conn.execute('INSERT INTO users (user_id, username, join_date) VALUES (?, ?, ?)', 
                 (uid, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    return True, "new_registered"

def get_balance(uid):
    conn = get_db_connection()
    user = conn.execute('SELECT points FROM users WHERE user_id = ?', (uid,)).fetchone()
    conn.close()
    return user['points'] if user else 0

# ----------------------------------------------------------
# 🏠 الـواجهة الـرئيسيـة
# ----------------------------------------------------------

@bot.message_handler(commands=['start'])
def send_welcome(m):
    uid = m.from_user.id
    access, reason = verify_user_access(uid, m.from_user.username)
    
    if not access:
        bot.send_message(m.chat.id, f"🚫 **نعتذر منك!**\n\nلقد وصل البوت للحد الأقصى من المستخدمين المسموح بهم ({MAX_USERS_LIMIT}).\nيرجى المحاولة لاحقاً أو التواصل مع المطور.")
        return

    pts = get_balance(uid)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📤 تـنـصـيـب مـشـروع", callback_data="btn_install"),
        types.InlineKeyboardButton("📂 مـشـاريـعـي", callback_data="btn_projects"),
        types.InlineKeyboardButton("💳 الـمـحـفـظـة", callback_data="btn_wallet"),
        types.InlineKeyboardButton("📡 حـالـة الـسـيـرفـر", callback_data="btn_server")
    )
    markup.add(
        types.InlineKeyboardButton("👨‍💻 الـمـطـور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}"),
        types.InlineKeyboardButton("📢 الـقـنـاة", url=f"https://t.me/{DEVELOPER_CHANNEL[1:]}")
    )
    
    if uid == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("⚙️ لـوحـة الإدارة الـعـلـيـا", callback_data="btn_admin"))

    text = f"""
— — — — — — — — — — — — — —
🎭 أهلاً بك في استضافة تايتان V37
— — — — — — — — — — — — — —
👤 الاسم: {m.from_user.first_name}
💰 رصيدك الحالي: `{pts}` نقطة
🆔 آيديك: `{uid}`
👥 عدد المشتركين: `{get_users_count()}/{MAX_USERS_LIMIT}`
— — — — — — — — — — — — — —
    """
    bot.send_message(m.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ----------------------------------------------------------
# 🔗 مـعـالـج الأزرار (Callback Handlers)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: True)
def global_callback_manager(c):
    uid = c.from_user.id
    mid = c.message.message_id
    cid = c.message.chat.id

    if c.data == "btn_install":
        if get_balance(uid) < 5:
            bot.answer_callback_query(c.id, "❌ رصيدك اقل من 5 نقاط!", show_alert=True)
        else:
            msg = bot.send_message(cid, "📤 **أرسل ملف البوت الآن (.py):**")
            bot.register_next_step_handler(msg, handle_file_upload)

    elif c.data == "btn_projects":
        conn = get_db_connection()
        bots = conn.execute('SELECT * FROM active_bots WHERE user_id = ?', (uid,)).fetchall()
        conn.close()
        txt = "📂 **مشاريعك:**\n\n" + ("لا توجد" if not bots else "\n".join([f"🤖 {b['bot_name']}" for b in bots]))
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_home"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    elif c.data == "btn_wallet":
        pts = get_balance(uid)
        txt = f"💳 **المحفظة**\n💰 الرصيد: `{pts}` نقطة"
        kb = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🎫 شحن كود", callback_data="redeem_code"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="go_home")
        )
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    elif c.data == "btn_server":
        info = f"📡 CPU: `{psutil.cpu_percent()}%` | RAM: `{psutil.virtual_memory().percent}%`"
        bot.edit_message_text(info, cid, mid, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_home")))

    elif c.data == "btn_admin" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🎫 توليد كود", callback_data="adm_gen"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="go_home")
        )
        bot.edit_message_text("⚙️ **لوحة الإدارة**", cid, mid, reply_markup=kb)

    elif c.data == "go_home":
        bot.delete_message(cid, mid)
        send_welcome(c)

# ----------------------------------------------------------
# 📁 مـعـالـجـة الـمـلـفـات (Next Steps)
# ----------------------------------------------------------

def handle_file_upload(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ خطأ في نوع الملف.")
        return
    bot.send_message(m.chat.id, "✅ تم استلام ملفك ومراجعته جارية...")

# 🏁 الـتـشـغـيل
if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    print(f"🚀 Titan V37 Limited ({MAX_USERS_LIMIT} Users) is Online!")
    bot.infinity_polling()
