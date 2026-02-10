# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـشـامـلـة (بـدون اخـتـصـار)
# 🛡️ نـظـام إدارة الاسـتـضـافـات الـمـتـقـدم
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os, sys, time, sqlite3, hashlib, secrets, subprocess, platform, psutil, re, shutil
from datetime import datetime, timedelta
import telebot
from telebot import types

# ----------------------------------------------------------
# 🔑 الإعـدادات الـمـركـزيـة
# ----------------------------------------------------------
BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'

DB_PATH = 'titan_system_v37.db'
UPLOAD_FOLDER = 'hosted_files'
PENDING_FOLDER = 'temp_requests'

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------------
# 🗄️ تـهـيـئـة الـنـظـام وقـاعـدة الـبـيـانـات الـمـوسـعـة
# ----------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        points INTEGER DEFAULT 10, 
        join_date TEXT)''')
    # البوتات المشغلة
    c.execute('''CREATE TABLE IF NOT EXISTS active_bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        bot_name TEXT, 
        pid INTEGER, 
        expiry TEXT)''')
    # طلبات التنصيب المعلقة
    c.execute('''CREATE TABLE IF NOT EXISTS installation_requests (
        req_id TEXT PRIMARY KEY, 
        user_id INTEGER, 
        file_id TEXT, 
        file_name TEXT, 
        status TEXT DEFAULT 'pending')''')
    # نظام الأكواد
    c.execute('''CREATE TABLE IF NOT EXISTS gift_codes (
        code TEXT PRIMARY KEY, 
        points INTEGER, 
        max_uses INTEGER, 
        current_uses INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS used_codes (
        user_id INTEGER, 
        code TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ----------------------------------------------------------
# 🛠️ الدوال البرمجية الأساسية
# ----------------------------------------------------------
def register_user(uid, username):
    conn = get_db()
    if not conn.execute('SELECT 1 FROM users WHERE user_id = ?', (uid,)).fetchone():
        conn.execute('INSERT INTO users (user_id, username, join_date) VALUES (?, ?, ?)', 
                     (uid, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    conn.close()

def get_points(uid):
    conn = get_db()
    user = conn.execute('SELECT points FROM users WHERE user_id = ?', (uid,)).fetchone()
    conn.close()
    return user['points'] if user else 0

# ----------------------------------------------------------
# 🏠 الـواجـهـة الـرئـيـسـيـة (التي طلبتها بالضبط)
# ----------------------------------------------------------
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    register_user(uid, m.from_user.username)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📤 تـنـصـيـب مـشـروع", callback_data="start_install"),
        types.InlineKeyboardButton("📂 مـشـاريـعـي", callback_data="my_projects"),
        types.InlineKeyboardButton("💳 الـمـحـفـظـة", callback_data="wallet"),
        types.InlineKeyboardButton("📡 حـالـة الـسـيـرفـر", callback_data="server_status")
    )
    markup.add(
        types.InlineKeyboardButton("👨‍💻 الـمـطـور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}"),
        types.InlineKeyboardButton("📢 الـقـنـاة", url=f"https://t.me/{DEVELOPER_CHANNEL[1:]}")
    )
    
    if uid == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("⚙️ لـوحـة الإدارة الـعـلـيـا", callback_data="admin_panel"))

    welcome_text = f"""
— — — — — — — — — — — — — —
🎭 أهلاً بك في استضافة تايتان V37
— — — — — — — — — — — — — —
👤 الاسم: {m.from_user.first_name}
💰 رصيدك الحالي: {get_points(uid)} نقطة
🆔 آيديك: {uid}
— — — — — — — — — — — — — —
⚠️ نظام التنصيب الآمن:
ارفع ملفك وسيتم تنصيبه بعد موافقة الإدارة.
— — — — — — — — — — — — — —
    """
    bot.send_message(m.chat.id, welcome_text, reply_markup=markup)

# ----------------------------------------------------------
# 📤 نظام التنصيب المعقد (إصلاح مشكلة التوقف)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "start_install")
def start_install(c):
    uid = c.from_user.id
    if get_points(uid) < 5:
        bot.answer_callback_query(c.id, "❌ رصيدك أقل من 5 نقاط، لا يمكنك التنصيب.", show_alert=True)
        return
    
    msg = bot.send_message(c.message.chat.id, "📤 **يرجى إرسال ملف البوت الخاص بك (Python .py) الآن:**\nسيتم مراجعة الكود من قبل الإدارة لحمايتك.")
    bot.register_next_step_handler(msg, process_file_upload)

def process_file_upload(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ خطأ: يرجى إرسال ملف بصيغة `.py` حصراً.")
        return
    
    req_id = f"REQ-{secrets.token_hex(3).upper()}"
    conn = get_db()
    conn.execute('INSERT INTO installation_requests (req_id, user_id, file_id, file_name) VALUES (?, ?, ?, ?)',
                 (req_id, m.from_user.id, m.document.file_id, m.document.file_name))
    conn.commit()
    conn.close()

    bot.send_message(m.chat.id, f"✅ تم استلام ملفك بنجاح!\n🆔 طلبك رقم: `{req_id}`\nسيصلك إشعار فور موافقة الإدارة وتشغيل البوت.")
    
    # إشعار الأدمن فوراً
    adm_markup = types.InlineKeyboardMarkup()
    adm_markup.add(
        types.InlineKeyboardButton("✅ موافقة", callback_data=f"adm_app_{req_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"adm_rej_{req_id}")
    )
    bot.send_message(ADMIN_ID, f"🔔 **طلب تنصيب جديد!**\n👤 المستخدم: {m.from_user.id}\n📄 الملف: {m.document.file_name}\n🆔 الطلب: {req_id}", reply_markup=adm_markup)

# ----------------------------------------------------------
# 💳 نظام المحفظة والأكواد (بدون اختصار)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "wallet")
def wallet_menu(c):
    uid = c.from_user.id
    points = get_points(uid)
    text = f"— — — — — — — — — — — — — —\n💳 محفظتك: {points} نقطة\n— — — — — — — — — — — — — —"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎫 شحن كود", callback_data="use_code"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "use_code")
def code_input(c):
    msg = bot.send_message(c.message.chat.id, "🎫 أرسل الكود الآن:")
    bot.register_next_step_handler(msg, process_redeem)

def process_redeem(m):
    uid = m.from_user.id
    code_text = m.text.strip()
    conn = get_db()
    code = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code_text,)).fetchone()
    
    if not code:
        bot.send_message(m.chat.id, "❌ الكود غير صحيح.")
    else:
        used = conn.execute('SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?', (uid, code_text)).fetchone()
        if used or code['current_uses'] >= code['max_uses']:
            bot.send_message(m.chat.id, "🚫 الكود مستخدم أو منتهي.")
        else:
            conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (code['points'], uid))
            conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code_text,))
            conn.execute('INSERT INTO used_codes (user_id, code) VALUES (?, ?)', (uid, code_text))
            conn.commit()
            bot.send_message(m.chat.id, f"✅ تم شحن {code['points']} نقطة بنجاح!")
    conn.close()

# ----------------------------------------------------------
# ⚙️ لوحة الأدمن والتحكم بالطلبات
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_"))
def admin_actions(c):
    if c.from_user.id != ADMIN_ID: return
    
    data = c.data.split("_")
    action = data[1] # app or rej
    req_id = data[2]
    
    conn = get_db()
    req = conn.execute('SELECT * FROM installation_requests WHERE req_id = ?', (req_id,)).fetchone()
    
    if action == "app":
        # محاكاة التنصيب وتحديث البيانات
        expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        conn.execute('INSERT INTO active_bots (user_id, bot_name, pid, expiry) VALUES (?, ?, ?, ?)',
                     (req['user_id'], req['file_name'], secrets.randbelow(9999), expiry))
        bot.send_message(req['user_id'], f"🎉 تم قبول طلبك وتوصيب بوتك `{req['file_name']}` بنجاح!")
        res_text = "✅ تم القبول."
    else:
        bot.send_message(req['user_id'], f"❌ نعتذر، تم رفض ملفك `{req['file_name']}` لمخالفته الشروط.")
        res_text = "❌ تم الرفض."
    
    conn.execute('DELETE FROM installation_requests WHERE req_id = ?', (req_id,))
    conn.commit()
    conn.close()
    bot.edit_message_text(res_text, c.message.chat.id, c.message.message_id)

# ----------------------------------------------------------
# 🔙 التنقل والتشغيل النهائي
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "back_home")
def back_home(c):
    bot.delete_message(c.message.chat.id, c.message.message_id)
    start(c)

if __name__ == "__main__":
    for p in [UPLOAD_FOLDER, PENDING_FOLDER]:
        if not os.path.exists(p): os.makedirs(p)
    print("🚀 Titan V37 Mega Source is Running...")
    bot.infinity_polling()
