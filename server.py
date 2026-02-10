# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـمـطـورة الـشـامـلـة
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

# مجلدات النظام
UPLOAD_FOLDER = 'hosted_bots_data'
PENDING_FOLDER = 'waiting_area'
DB_PATH = 'titan_v37_final.db'

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------------
# 🗄️ تـهـيـئـة قـاعـدة الـبـيـانـات الـمـوسـعـة
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
        points INTEGER DEFAULT 5, 
        join_date TEXT, 
        is_banned INTEGER DEFAULT 0)''')
    # جدول البوتات النشطة
    c.execute('''CREATE TABLE IF NOT EXISTS active_bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        bot_name TEXT, 
        process_id INTEGER, 
        expiry_time TEXT, 
        status TEXT)''')
    # جدول طلبات التنصيب
    c.execute('''CREATE TABLE IF NOT EXISTS installation_requests (
        req_id TEXT PRIMARY KEY, 
        user_id INTEGER, 
        file_name TEXT, 
        temp_path TEXT, 
        days INTEGER, 
        cost INTEGER, 
        request_time TEXT)''')
    # جدول الأكواد المتعددة
    c.execute('''CREATE TABLE IF NOT EXISTS gift_codes (
        code TEXT PRIMARY KEY, 
        points INTEGER, 
        max_uses INTEGER, 
        current_uses INTEGER DEFAULT 0)''')
    # سجل استخدام الأكواد
    c.execute('''CREATE TABLE IF NOT EXISTS used_codes (
        user_id INTEGER, 
        code TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ----------------------------------------------------------
# 🛠️ الـدوال الـمـنـطقـيـة لـلـنـظـام
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
# ⚙️ لـوحـة الإدارة (Admin Control Center)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_panel(c):
    if c.from_user.id != ADMIN_ID: return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📥 إدارة الـطـلـبـات", callback_data="adm_view_reqs"),
        types.InlineKeyboardButton("👥 إدارة الـمـسـتـخـدمـيـن", callback_data="adm_manage_users"),
        types.InlineKeyboardButton("🎫 تـولـيـد أكـواد", callback_data="adm_gen_codes"),
        types.InlineKeyboardButton("📊 إحـصـائـيـات الـسـيـرفـر", callback_data="server_status"),
        types.InlineKeyboardButton("🔙 رجـوع", callback_data="back_home")
    )
    bot.edit_message_text("⚙️ **مـركـز الإدارة الـشـامـل:**\nتحكم بالمستخدمين والطلبات والأكواد.", 
                          c.message.chat.id, c.message.message_id, reply_markup=markup)

# 1. إدارة المستخدمين (إضافة/خصم نقاط)
@bot.callback_query_handler(func=lambda c: c.data == "adm_manage_users")
def adm_users_start(c):
    msg = bot.send_message(c.message.chat.id, "👤 أرسل آيدي المستخدم للتحكم برصيده:")
    bot.register_next_step_handler(msg, adm_users_process)

def adm_users_process(m):
    if not m.text.isdigit(): return
    uid = int(m.text)
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    conn.close()
    
    if not user:
        bot.send_message(m.chat.id, "❌ المستخدم غير مسجل.")
        return
        
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"set_add_{uid}"),
        types.InlineKeyboardButton("➖ خصم نقاط", callback_data=f"set_sub_{uid}")
    )
    bot.send_message(m.chat.id, f"👤 المستخدم: `{uid}`\n💰 الرصيد الحالي: `{user['points']}`", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith(("set_add_", "set_sub_")))
def adm_points_final(c):
    action, uid = c.data.split("_")[1], c.data.split("_")[2]
    msg = bot.send_message(c.message.chat.id, f"🔢 أرسل عدد النقاط للـ {'إضافة' if action=='add' else 'خصم'}:")
    bot.register_next_step_handler(msg, lambda m: finalize_points(m, uid, action))

def finalize_points(m, uid, action):
    if not m.text.isdigit(): return
    amount = int(m.text) if action == 'add' else -int(m.text)
    conn = get_db()
    conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (amount, uid))
    conn.commit()
    conn.close()
    bot.send_message(m.chat.id, "✅ تم التحديث بنجاح.")

# 2. توليد أكواد (لعدد محدد من الأشخاص)
@bot.callback_query_handler(func=lambda c: c.data == "adm_gen_codes")
def adm_gen_codes(c):
    msg = bot.send_message(c.message.chat.id, "🎫 أرسل (النقاط : عدد الأشخاص)\nمثال: `50:10` لنشر كود بـ 50 نقطة لـ 10 مستخدمين.")
    bot.register_next_step_handler(msg, adm_gen_process)

def adm_gen_process(m):
    try:
        pts, uses = m.text.split(":")
        code = f"TITAN-{secrets.token_hex(3).upper()}"
        conn = get_db()
        conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(pts), int(uses)))
        conn.commit()
        conn.close()
        bot.send_message(m.chat.id, f"✅ **تم إنشاء الكود:**\n`{code}`\n💰 النقاط: {pts} | 👥 لـ {uses} أشخاص")
    except: bot.send_message(m.chat.id, "❌ خطأ في التنسيق.")

# ----------------------------------------------------------
# 📂 مـشـاريـعـي والـروابـط الـتـلقـائـيـة
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
        # حساب الوقت المتبقي
        exp = datetime.strptime(b['expiry_time'], '%Y-%m-%d %H:%M:%S')
        rem = exp - datetime.now()
        # توليد رابط API تلقائي مشفر
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
# 📊 حـالـة الـسـيـرفـر (Real Stats)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "server_status")
def server_status(c):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    uptime = str(timedelta(seconds=int(time.time() - psutil.boot_time())))
    
    conn = get_db()
    users = conn.execute('SELECT count(*) FROM users').fetchone()[0]
    active = conn.execute('SELECT count(*) FROM active_bots').fetchone()[0]
    conn.close()
    
    status_text = f"""
— — — — — — — — — — — — — —
📡 حالة سيرفر تايتان V37
— — — — — — — — — — — — — —
⚙️ استهلاك المعالج: {cpu}%
🧠 استهلاك الرام: {ram}%
💽 مساحة القرص: {disk}%
⏱️ وقت التشغيل: {uptime}
━━━━━━━━━━━━━━━
👥 مستخدمين النظام: {users}
🤖 بوتات مستضافة: {active}
— — — — — — — — — — — — — —
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="server_status"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text(status_text, c.message.chat.id, c.message.message_id, reply_markup=markup)

# ----------------------------------------------------------
# 🔙 التنقل والرجوع
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "back_home")
def back_home(c):
    bot.delete_message(c.message.chat.id, c.message.message_id)
    start(c)

# 🏁 تشغيل البوت
if __name__ == "__main__":
    for folder in [UPLOAD_FOLDER, PENDING_FOLDER]:
        if not os.path.exists(folder): os.makedirs(folder)
    print("🔥 Titan V37 Mega Pro is Running...")
    bot.infinity_polling()
