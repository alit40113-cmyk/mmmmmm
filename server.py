# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - نـظـام بـلاك تـيـك الـمـطـور
# 🛡️ نـظـام الـتـنـصـيـب بـعـد مـوافـقـة الأدمن (ضـد الـثـغـرات)
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

DB_PATH = 'titan_v37_mega.db'
UPLOAD_FOLDER = 'hosted_bots_data'
PENDING_FOLDER = 'waiting_area'
LOG_FILE = 'titan_system.log'

# إعداد السجلات (Logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("Titan-V37")

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------------
# 🗄️ تـهـيـئـة الـنـظـام وقـاعـدة الـبـيـانـات
# ----------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        points INTEGER DEFAULT 10, 
        join_date TEXT, 
        is_banned INTEGER DEFAULT 0
    )''')
    # جدول البوتات المشغلة
    c.execute('''CREATE TABLE IF NOT EXISTS active_bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        bot_name TEXT, 
        process_id INTEGER, 
        expiry_time TEXT, 
        status TEXT DEFAULT 'running',
        auth_token TEXT
    )''')
    # جدول طلبات التنصيب
    c.execute('''CREATE TABLE IF NOT EXISTS installation_requests (
        req_id TEXT PRIMARY KEY, 
        user_id INTEGER, 
        file_id TEXT, 
        file_name TEXT, 
        upload_time TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    # جدول الأكواد
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
    logger.info("Database initialized successfully.")

init_db()

# ----------------------------------------------------------
# 🛠️ الـدوال الـمـسـاعـدة والـحـمـايـة
# ----------------------------------------------------------

def register_user(uid, username):
    conn = get_db()
    if not conn.execute('SELECT 1 FROM users WHERE user_id = ?', (uid,)).fetchone():
        conn.execute('INSERT INTO users (user_id, username, join_date) VALUES (?, ?, ?)', 
                     (uid, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    conn.close()

def get_user_points(uid):
    conn = get_db()
    res = conn.execute('SELECT points FROM users WHERE user_id = ?', (uid,)).fetchone()
    conn.close()
    return res['points'] if res else 0

def check_banned(uid):
    conn = get_db()
    res = conn.execute('SELECT is_banned FROM users WHERE user_id = ?', (uid,)).fetchone()
    conn.close()
    return res['is_banned'] if res else 0

# ----------------------------------------------------------
# 🏠 الـواجـهـة الـرئـيـسـيـة (الـتـصـمـيـم الأصلي)
# ----------------------------------------------------------

@bot.message_handler(commands=['start'])
def start_handler(m):
    uid = m.from_user.id
    if check_banned(uid):
        bot.send_message(m.chat.id, "🚫 عذراً، لقد تم حظرك من استخدام النظام.")
        return

    register_user(uid, m.from_user.username)
    points = get_user_points(uid)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_install = types.InlineKeyboardButton("📤 تـنـصـيـب مـشـروع", callback_data="start_install")
    btn_projects = types.InlineKeyboardButton("📂 مـشـاريـعـي", callback_data="my_projects")
    btn_wallet = types.InlineKeyboardButton("💳 الـمـحـفـظـة", callback_data="wallet_main")
    btn_status = types.InlineKeyboardButton("📡 حـالـة الـسـيـرفـر", callback_data="server_health")
    
    dev_btn = types.InlineKeyboardButton("👨‍💻 الـمـطـور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    chn_btn = types.InlineKeyboardButton("📢 الـقـنـاة", url=f"https://t.me/{DEVELOPER_CHANNEL[1:]}")
    
    markup.add(btn_install, btn_projects, btn_wallet, btn_status)
    markup.add(dev_btn, chn_btn)
    
    if uid == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("⚙️ لـوحـة الإدارة الـعـلـيـا", callback_data="admin_home"))

    welcome_text = f"""
— — — — — — — — — — — — — —
🎭 أهلاً بك في استضافة تايتان V37
— — — — — — — — — — — — — —
👤 الاسم: {m.from_user.first_name}
💰 رصيدك الحالي: `{points}` نقطة
🆔 آيديك: `{uid}`
— — — — — — — — — — — — — —
⚠️ نظام التنصيب الآمن:
ارفع ملفك وسيتم تنصيبه بعد موافقة الإدارة.
— — — — — — — — — — — — — —
    """
    bot.send_message(m.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# ----------------------------------------------------------
# 📥 نـظـام الـتـنـصـيـب الـمـوسـع (Step by Step)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "start_install")
def install_init(c):
    uid = c.from_user.id
    if get_user_points(uid) < 5:
        bot.answer_callback_query(c.id, "❌ رصيدك غير كافٍ (تحتاج 5 نقاط على الأقل).", show_alert=True)
        return
    
    msg = bot.send_message(c.message.chat.id, "📤 **يرجى إرسال ملف البوت الخاص بك الآن بصيغة (.py):**")
    bot.register_next_step_handler(msg, process_file_step)

def process_file_step(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ خطأ: يجب إرسال ملف برمجية ينتهي بـ `.py` حصراً.")
        return

    req_id = secrets.token_hex(4).upper()
    conn = get_db()
    conn.execute('''INSERT INTO installation_requests (req_id, user_id, file_id, file_name, upload_time) 
                    VALUES (?, ?, ?, ?, ?)''', 
                 (req_id, m.from_user.id, m.document.file_id, m.document.file_name, datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit()
    conn.close()

    bot.send_message(m.chat.id, f"✅ **تم استلام طلبك بنجاح!**\n🆔 رقم الطلب: `{req_id}`\n⏳ سيتم مراجعته من قبل الإدارة.")
    
    # إخطار الإدارة
    admin_kb = types.InlineKeyboardMarkup()
    admin_kb.add(types.InlineKeyboardButton("✅ موافقة", callback_data=f"adm_app_{req_id}"),
                 types.InlineKeyboardButton("❌ رفض", callback_data=f"adm_rej_{req_id}"))
    bot.send_message(ADMIN_ID, f"🔔 **طلب تنصيب جديد!**\n👤 من: {m.from_user.id}\n📄 الملف: {m.document.file_name}\n🆔 الطلب: {req_id}", reply_markup=admin_kb)

# ----------------------------------------------------------
# 💳 نـظـام الـمـحـفـظـة الـشـامـل (Wallet)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "wallet_main")
def wallet_main(c):
    uid = c.from_user.id
    points = get_user_points(uid)
    text = f"💳 **مـحـفـظـتـك الـرقمـيـة**\n\n💰 رصيدك الحالي: `{points}` نقطة\n📢 يمكنك استخدام النقاط لتشغيل أو تمديد البوتات."
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎫 استخدام كود هدية", callback_data="redeem_gift"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start"))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "redeem_gift")
def redeem_init(c):
    msg = bot.send_message(c.message.chat.id, "🎫 **أرسل كود الهدية الآن:**")
    bot.register_next_step_handler(msg, redeem_process)

def redeem_process(m):
    uid = m.from_user.id
    code_txt = m.text.strip()
    conn = get_db()
    code_data = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code_txt,)).fetchone()
    
    if not code_data:
        bot.send_message(m.chat.id, "❌ الكود غير صحيح.")
    elif code_data['current_uses'] >= code_data['max_uses']:
        bot.send_message(m.chat.id, "🚫 هذا الكود وصل للحد الأقصى للاستخدام.")
    else:
        used = conn.execute('SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?', (uid, code_txt)).fetchone()
        if used:
            bot.send_message(m.chat.id, "⚠️ لقد استخدمت هذا الكود من قبل!")
        else:
            conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (code_data['points'], uid))
            conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code_txt,))
            conn.execute('INSERT INTO used_codes (user_id, code, use_time) VALUES (?, ?, ?)', 
                         (uid, code_txt, datetime.now().strftime('%Y-%m-%d %H:%M')))
            conn.commit()
            bot.send_message(m.chat.id, f"✅ تم تفعيل الكود! حصلت على `{code_data['points']}` نقطة.")
    conn.close()

# ----------------------------------------------------------
# ⚙️ لـوحـة الإدارة الـعـلـيـا (Full Features)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "admin_home")
def admin_home(c):
    if c.from_user.id != ADMIN_ID: return
    conn = get_db()
    total_users = conn.execute('SELECT count(*) FROM users').fetchone()[0]
    total_bots = conn.execute('SELECT count(*) FROM active_bots').fetchone()[0]
    conn.close()
    
    text = f"⚙️ **لوحة التحكم العليا**\n\n👥 عدد المستخدمين: `{total_users}`\n🤖 البوتات النشطة: `{total_bots}`"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎫 توليد أكواد", callback_data="adm_gen_code"),
        types.InlineKeyboardButton("📤 الطلبات المعلقة", callback_data="adm_view_reqs"),
        types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "adm_gen_code")
def gen_code_init(c):
    msg = bot.send_message(c.message.chat.id, "🎫 أرسل (النقاط : عدد الأشخاص) مثال `100:5`:")
    bot.register_next_step_handler(msg, gen_code_finalize)

def gen_code_finalize(m):
    try:
        pts, uses = m.text.split(":")
        code = f"TITAN-{secrets.token_hex(3).upper()}"
        conn = get_db()
        conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(pts), int(uses)))
        conn.commit()
        conn.close()
        bot.send_message(m.chat.id, f"✅ تم إنشاء الكود: `{code}`")
    except:
        bot.send_message(m.chat.id, "❌ خطأ في التنسيق.")

# ----------------------------------------------------------
# 🔙 دوال الـتـنـقل والـتـشـغيل
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "back_to_start")
def back_to_start(c):
    bot.delete_message(c.message.chat.id, c.message.message_id)
    start_handler(c)

@bot.callback_query_handler(func=lambda c: c.data == "server_health")
def server_health(c):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    uptime = str(timedelta(seconds=int(time.time() - psutil.boot_time())))
    
    text = f"📡 **حـالـة الـسـيـرفـر**\n\n⚙️ استهلاك المعالج: `{cpu}%`\n🧠 استهلاك الرام: `{ram}%`\n⏱️ وقت التشغيل: `{uptime}`"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start"))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    logger.info("Titan V37 is starting...")
    bot.infinity_polling()
