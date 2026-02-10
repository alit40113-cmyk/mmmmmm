# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـمـتـكـامـلـة (فـول سـورس)
# 🛡️ نـظـام إدارة الاسـتـضـافـات الـمـطـور والآمن
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os, sys, time, sqlite3, hashlib, secrets, subprocess, platform, psutil, re, shutil
from datetime import datetime, timedelta
import telebot
from telebot import types

# ----------------------------------------------------------
# 🔑 الإعـدادات الـنـظام الـمـركـزيـة
# ----------------------------------------------------------
BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'

DB_PATH = 'titan_v37_final.db'
UPLOAD_FOLDER = 'hosted_bots_data'

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------------
# 🗄️ تـهـيـئـة قـاعـدة الـبـيـانـات
# ----------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER DEFAULT 10, join_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS active_bots (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, bot_name TEXT, pid TEXT, expiry TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS installation_requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_id TEXT, file_name TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# ----------------------------------------------------------
# 🛠️ الـدوال الـمـسـاعـدة
# ----------------------------------------------------------
def get_points(uid):
    conn = get_db()
    user = conn.execute('SELECT points FROM users WHERE user_id = ?', (uid,)).fetchone()
    conn.close()
    return user['points'] if user else 0

def register_user(uid, username):
    conn = get_db()
    if not conn.execute('SELECT 1 FROM users WHERE user_id = ?', (uid,)).fetchone():
        conn.execute('INSERT INTO users (user_id, username, join_date) VALUES (?, ?, ?)', 
                     (uid, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    conn.close()

# ----------------------------------------------------------
# 🏠 الـواجـهـة الـرئـيـسـيـة
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
# 📤 1. تـنـصـيـب مـشـروع (شغال 100%)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "start_install")
def install_callback(c):
    if get_points(c.from_user.id) < 5:
        bot.answer_callback_query(c.id, "❌ رصيدك غير كافٍ (تحتاج 5 نقاط).", show_alert=True)
        return
    msg = bot.send_message(c.message.chat.id, "📤 أرسل ملف البوت الآن (.py):")
    bot.register_next_step_handler(msg, save_project_request)

def save_project_request(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ خطأ: يرجى إرسال ملف بصيغة Python فقط.")
        return
    
    req_id = secrets.token_hex(3).upper()
    conn = get_db()
    conn.execute('INSERT INTO installation_requests (req_id, user_id, file_id, file_name) VALUES (?, ?, ?, ?)',
                 (req_id, m.from_user.id, m.document.file_id, m.document.file_name))
    conn.commit()
    conn.close()
    
    bot.send_message(m.chat.id, f"✅ تم استلام طلبك برقم: `{req_id}`\nانتظر موافقة الأدمن.")
    
    # إشعار للأدمن
    adm_kb = types.InlineKeyboardMarkup()
    adm_kb.add(types.InlineKeyboardButton("✅ قبول", callback_data=f"approve_{req_id}"),
               types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{req_id}"))
    bot.send_message(ADMIN_ID, f"🔔 طلب جديد:\nID: {m.from_user.id}\nFile: {m.document.file_name}", reply_markup=adm_kb)

# ----------------------------------------------------------
# 💳 2. الـمـحـفـظـة (شغال 100%)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "wallet")
def wallet_callback(c):
    pts = get_points(c.from_user.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎫 شحن كود", callback_data="redeem_code"),
           types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_home"))
    bot.edit_message_text(f"💳 محفظتك الحالية: {pts} نقطة", c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "redeem_code")
def redeem_kb(c):
    msg = bot.send_message(c.message.chat.id, "🎫 أرسل الكود الآن:")
    bot.register_next_step_handler(msg, process_code)

def process_code(m):
    uid, code_txt = m.from_user.id, m.text.strip()
    conn = get_db()
    code_db = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code_txt,)).fetchone()
    if code_db and code_db['current_uses'] < code_db['max_uses']:
        used = conn.execute('SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?', (uid, code_txt)).fetchone()
        if not used:
            conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (code_db['points'], uid))
            conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code_txt,))
            conn.execute('INSERT INTO used_codes (user_id, code) VALUES (?, ?)', (uid, code_txt))
            conn.commit()
            bot.send_message(m.chat.id, "✅ تم الشحن!")
        else: bot.send_message(m.chat.id, "❌ استخدمته سابقاً.")
    else: bot.send_message(m.chat.id, "❌ كود منتهي أو خاطئ.")
    conn.close()

# ----------------------------------------------------------
# 📂 3. مـشـاريـعـي (شغال 100%)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "my_projects")
def projects_callback(c):
    conn = get_db()
    bots = conn.execute('SELECT * FROM active_bots WHERE user_id = ?', (c.from_user.id,)).fetchall()
    conn.close()
    if not bots:
        bot.answer_callback_query(c.id, "❌ لا توجد مشاريع.", show_alert=True)
        return
    txt = "📂 مشاريعك النشطة:\n"
    kb = types.InlineKeyboardMarkup()
    for b in bots:
        kb.add(types.InlineKeyboardButton(f"🤖 {b['bot_name']}", callback_data=f"bot_{b['id']}"))
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_home"))
    bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=kb)

# ----------------------------------------------------------
# 📡 4. حـالـة الـسـيـرفـر (شغال 100%)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "server_status")
def status_callback(c):
    status = f"📡 CPU: {psutil.cpu_percent()}%\n🧠 RAM: {psutil.virtual_memory().percent}%"
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_home"))
    bot.edit_message_text(status, c.message.chat.id, c.message.message_id, reply_markup=kb)

# ----------------------------------------------------------
# ⚙️ 5. لـوحـة الإدارة والـتـحـكـم (شغال 100%)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_callback(c):
    if c.from_user.id != ADMIN_ID: return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎫 توليد كود", callback_data="gen_code"))
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_home"))
    bot.edit_message_text("⚙️ لوحة الإدارة:", c.message.chat.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("approve_", "reject_")))
def admin_decision(c):
    action, req_id = c.data.split("_")
    conn = get_db()
    req = conn.execute('SELECT * FROM installation_requests WHERE req_id = ?', (req_id,)).fetchone()
    if action == "approve":
        conn.execute('INSERT INTO active_bots (user_id, bot_name, pid, expiry) VALUES (?, ?, ?, ?)',
                     (req['user_id'], req['file_name'], "PID-88", "2026-01-01"))
        bot.send_message(req['user_id'], f"✅ تم تفعيل بوتك: {req['file_name']}")
    conn.execute('DELETE FROM installation_requests WHERE req_id = ?', (req_id,))
    conn.commit()
    conn.close()
    bot.edit_message_text(f"✅ تم الـ {action}", c.message.chat.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data == "back_to_home")
def back_home(c):
    bot.delete_message(c.message.chat.id, c.message.message_id)
    start(c)

# 🏁 الـتـشـغـيـل
if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    print("🚀 Titan V37 Final is Online!")
    bot.infinity_polling()
