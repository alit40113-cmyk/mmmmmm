# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـمـوسـعـة والـنـهـائـيـة
# 🛡️ نـظـام إدارة الاسـتـضـافـات الـشـامـل والآمن
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

DB_PATH = 'titan_v37_mega.db'
UPLOAD_FOLDER = 'hosted_bots_data'
PENDING_FOLDER = 'waiting_area'

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
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER DEFAULT 5, join_date TEXT, is_banned INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS active_bots (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, bot_name TEXT, process_id INTEGER, expiry_time TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# ----------------------------------------------------------
# 🛠️ الـدوال الـمـسـاعـدة
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
# 🏠 الـواجـهـة الـرئـيـسـيـة (الـتـصـمـيـم الـمـطـلـوب)
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
# 💳 نـظـام الـمـحـفـظـة (Wallet Logic)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "wallet")
def wallet_menu(c):
    uid = c.from_user.id
    points = get_points(uid)
    
    wallet_text = f"""
— — — — — — — — — — — — — —
💳 مـحـفـظـتـك الـرقـمـيـة
— — — — — — — — — — — — — —
💰 رصيدك الحالي: {points} نقطة
🆔 آيديك: {uid}
— — — — — — — — — — — — — —
📢 يمكنك استخدام النقاط لتمديد استضافة بوتاتك.
— — — — — — — — — — — — — —
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎫 استخدام كود هدية", callback_data="use_gift_code"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text(wallet_text, c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "use_gift_code")
def ask_for_code(c):
    msg = bot.send_message(c.message.chat.id, "🎫 أرسل كود الهدية الآن:")
    bot.register_next_step_handler(msg, process_gift_code)

def process_gift_code(m):
    uid = m.from_user.id
    code_text = m.text.strip()
    conn = get_db()
    code_data = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code_text,)).fetchone()
    
    if not code_data:
        bot.send_message(m.chat.id, "❌ الكود غير صحيح أو انتهت صلاحيته.")
    else:
        used = conn.execute('SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?', (uid, code_text)).fetchone()
        if used:
            bot.send_message(m.chat.id, "⚠️ لقد استخدمت هذا الكود من قبل!")
        elif code_data['current_uses'] >= code_data['max_uses']:
            bot.send_message(m.chat.id, "🚫 هذا الكود وصل للحد الأقصى من الاستخدام.")
        else:
            conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (code_data['points'], uid))
            conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code_text,))
            conn.execute('INSERT INTO used_codes (user_id, code) VALUES (?, ?)', (uid, code_text))
            conn.commit()
            bot.send_message(m.chat.id, f"✅ تم تفعيل الكود بنجاح! مبروك حصلت على {code_data['points']} نقطة.")
    conn.close()

# ----------------------------------------------------------
# 📂 مـشـاريـعـي والـروابـط
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "my_projects")
def my_projects_list(c):
    uid = c.from_user.id
    conn = get_db()
    bots = conn.execute('SELECT * FROM active_bots WHERE user_id = ?', (uid,)).fetchall()
    conn.close()
    
    if not bots:
        bot.answer_callback_query(c.id, "❌ ليس لديك مشاريع نشطة حالياً.", show_alert=True)
        return
        
    markup = types.InlineKeyboardMarkup()
    for b in bots:
        markup.add(types.InlineKeyboardButton(f"🤖 {b['bot_name']}", callback_data=f"view_bot_{b['id']}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text("📂 **مشاريعك المستضافة:**", c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("view_bot_"))
def view_bot_details(c):
    bid = c.data.split("_")[2]
    conn = get_db()
    b = conn.execute('SELECT * FROM active_bots WHERE id = ?', (bid,)).fetchone()
    conn.close()
    
    if b:
        exp = datetime.strptime(b['expiry_time'], '%Y-%m-%d %H:%M:%S')
        rem = exp - datetime.now()
        token = hashlib.md5(str(b['user_id']).encode()).hexdigest()[:8]
        api_link = f"https://titan-v37.net/api/connect?pid={b['process_id']}&auth={token}"
        
        details = f"""
— — — — — — — — — — — — — —
🤖 تفاصيل المشروع: {b['bot_name']}
— — — — — — — — — — — — — —
⏱️ المتبقي: {rem.days} يوم و {rem.seconds//3600} ساعة
🆔 العملية (PID): {b['process_id']}
🌐 الحالة: قيد التشغيل ✅

🔗 رابط الاتصال التلقائي:
`{api_link}`
— — — — — — — — — — — — — —
        """
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 إيقاف المشروع", callback_data=f"stop_{b['id']}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="my_projects"))
        bot.edit_message_text(details, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")

# ----------------------------------------------------------
# 📊 حـالـة الـسـيـرفـر
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "server_status")
def server_status(c):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    uptime = str(timedelta(seconds=int(time.time() - psutil.boot_time())))
    
    status_text = f"""
— — — — — — — — — — — — — —
📡 حالة سيرفر تايتان V37
— — — — — — — — — — — — — —
⚙️ استهلاك المعالج: {cpu}%
🧠 استهلاك الرام: {ram}%
⏱️ وقت التشغيل: {uptime}
— — — — — — — — — — — — — —
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="server_status"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text(status_text, c.message.chat.id, c.message.message_id, reply_markup=markup)

# ----------------------------------------------------------
# ⚙️ لـوحـة الإدارة (Admin Panel)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_panel(c):
    if c.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="adm_users"),
        types.InlineKeyboardButton("🎫 توليد أكواد", callback_data="adm_gen_code"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
    )
    bot.edit_message_text("⚙️ **لوحة التحكم العليا:**", c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "adm_gen_code")
def adm_gen_code_start(c):
    msg = bot.send_message(c.message.chat.id, "🎫 أرسل (النقاط : عدد الأشخاص) مثال `100:5`:")
    bot.register_next_step_handler(msg, finalize_gen_code)

def finalize_gen_code(m):
    try:
        pts, uses = m.text.split(":")
        code = f"TITAN-{secrets.token_hex(3).upper()}"
        conn = get_db()
        conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(pts), int(uses)))
        conn.commit()
        conn.close()
        bot.send_message(m.chat.id, f"✅ تم إنشاء الكود: `{code}`")
    except: bot.send_message(m.chat.id, "❌ خطأ في التنسيق.")

# ----------------------------------------------------------
# 🔙 التنقل والتشغيل
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "back_home")
def back_home(c):
    bot.delete_message(c.message.chat.id, c.message.message_id)
    start(c)

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    print("🔥 Titan V37 Mega Pro is Online!")
    bot.infinity_polling()
