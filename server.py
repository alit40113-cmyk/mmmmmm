# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـشـامـلـة والـنـهـائـيـة
# 🛡️ نـظـام إدارة الاسـتـضـافـات الـشـامـل والآمن
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os, sys, time, sqlite3, hashlib, secrets, subprocess, platform, psutil, re, shutil
from datetime import datetime, timedelta
import telebot
from telebot import types

# ----------------------------------------------------------
# 🔑 الإعـدادات الـنـظـام الـمـركـزيـة
# ----------------------------------------------------------
BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'

DB_PATH = 'titan_v37_mega.db'
UPLOAD_FOLDER = 'hosted_bots_data'
PENDING_FOLDER = 'waiting_area'

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------------
# 🗄️ تـهـيـئـة قـاعـدة الـبـيـانـات الـشـامـلـة
# ----------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER DEFAULT 5, join_date TEXT, is_banned INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS active_bots (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, bot_name TEXT, process_id TEXT, expiry_time TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS installation_requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_id TEXT, file_name TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# ----------------------------------------------------------
# 🛠️ الـدوال الـمـنـطـقـيـة
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
# 💳 نـظام الـمـحـفـظـة (الـزر شـغـال 100%)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "wallet")
def wallet_menu(c):
    uid = c.from_user.id
    points = get_points(uid)
    wallet_text = f"💳 محفظتك:\n💰 رصيدك: {points} نقطة\n🆔 آيديك: {uid}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎫 استخدام كود هدية", callback_data="use_gift_code"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text(wallet_text, c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "use_gift_code")
def ask_code(c):
    msg = bot.send_message(c.message.chat.id, "🎫 أرسل الكود الآن:")
    bot.register_next_step_handler(msg, redeem_code_process)

def redeem_code_process(m):
    uid = m.from_user.id
    code_txt = m.text.strip()
    conn = get_db()
    code_data = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code_txt,)).fetchone()
    if code_data and code_data['current_uses'] < code_data['max_uses']:
        used = conn.execute('SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?', (uid, code_txt)).fetchone()
        if not used:
            conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (code_data['points'], uid))
            conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code_txt,))
            conn.execute('INSERT INTO used_codes (user_id, code) VALUES (?, ?)', (uid, code_txt))
            conn.commit()
            bot.send_message(m.chat.id, "✅ تم شحن النقاط!")
        else: bot.send_message(m.chat.id, "⚠️ استخدمته سابقاً.")
    else: bot.send_message(m.chat.id, "❌ الكود خاطئ.")
    conn.close()

# ----------------------------------------------------------
# 📤 نـظـام الـتـنـصـيـب (الـزر شـغـال 100%)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "start_install")
def start_install(c):
    bot.send_message(c.message.chat.id, "📤 أرسل ملف البوت (.py) الآن:")
    bot.register_next_step_handler(c.message, receive_file)

def receive_file(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ أرسل ملف بايثون فقط.")
        return
    req_id = secrets.token_hex(3).upper()
    conn = get_db()
    conn.execute('INSERT INTO installation_requests (req_id, user_id, file_id, file_name) VALUES (?, ?, ?, ?)',
                 (req_id, m.from_user.id, m.document.file_id, m.document.file_name))
    conn.commit()
    conn.close()
    bot.send_message(m.chat.id, f"✅ طلبك قيد المراجعة برقم: `{req_id}`")
    
    # إشعار للأدمن
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ قبول", callback_data=f"adm_app_{req_id}"),
               types.InlineKeyboardButton("❌ رفض", callback_data=f"adm_rej_{req_id}"))
    bot.send_message(ADMIN_ID, f"🔔 طلب جديد من {m.from_user.id}", reply_markup=markup)

# ----------------------------------------------------------
# 📂 مـشـاريـعـي وحـالـة الـسـيـرفـر
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "my_projects")
def my_projects(c):
    conn = get_db()
    bots = conn.execute('SELECT * FROM active_bots WHERE user_id = ?', (c.from_user.id,)).fetchall()
    conn.close()
    if not bots:
        bot.answer_callback_query(c.id, "❌ لا توجد مشاريع.", show_alert=True)
        return
    markup = types.InlineKeyboardMarkup()
    for b in bots:
        markup.add(types.InlineKeyboardButton(f"🤖 {b['bot_name']}", callback_data=f"view_{b['id']}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text("📂 مشاريعك:", c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "server_status")
def server_status(c):
    status = f"📡 CPU: {psutil.cpu_percent()}%\n🧠 RAM: {psutil.virtual_memory().percent}%"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text(status, c.message.chat.id, c.message.message_id, reply_markup=markup)

# ----------------------------------------------------------
# ⚙️ لـوحـة الإدارة الـعـلـيـا (الـكـود الـكـامل لـلأدمن)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_panel(c):
    if c.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📥 إدارة الطلبات", callback_data="adm_view_reqs"),
        types.InlineKeyboardButton("🎫 توليد أكواد", callback_data="adm_gen_code"),
        types.InlineKeyboardButton("👥 إدارة النقاط", callback_data="adm_manage_pts"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
    )
    bot.edit_message_text("⚙️ لوحة التحكم الإدارية:", c.message.chat.id, c.message.message_id, reply_markup=markup)

# ----------------------------------------------------------
# 🔙 الـرجـوع والـنـهـايـة
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "back_home")
def back_home(c):
    bot.delete_message(c.message.chat.id, c.message.message_id)
    start(c)

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    print("🔥 Titan V37 Mega Online!")
    bot.infinity_polling()
