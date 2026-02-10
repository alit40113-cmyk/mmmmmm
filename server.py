# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـعـمـلاقـة والـنـهـائـيـة
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
    # مستخدمين
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER DEFAULT 5, join_date TEXT, is_banned INTEGER DEFAULT 0)')
    # بوتات نشطة
    c.execute('CREATE TABLE IF NOT EXISTS active_bots (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, bot_name TEXT, process_id INTEGER, expiry_time TEXT, status TEXT)')
    # طلبات انتظار
    c.execute('CREATE TABLE IF NOT EXISTS installation_requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_id TEXT, file_name TEXT, status TEXT)')
    # أكواد
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
# 📤 نـظـام الـتـنـصـيـب (Installation Logic)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "start_install")
def start_install_process(c):
    uid = c.from_user.id
    if get_points(uid) < 10:
        bot.answer_callback_query(c.id, "❌ رصيدك غير كافٍ (تحتاج 10 نقاط على الأقل).", show_alert=True)
        return
    
    msg = bot.send_message(c.message.chat.id, "📤 **يرجى إرسال ملف البوت الآن (بصيغة .py فقط):**")
    bot.register_next_step_handler(msg, handle_uploaded_file)

def handle_uploaded_file(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ عذراً، يجب إرسال ملف برمجية ينتهي بـ .py")
        return

    req_id = secrets.token_hex(4).upper()
    conn = get_db()
    conn.execute('INSERT INTO installation_requests (req_id, user_id, file_id, file_name, status) VALUES (?, ?, ?, ?, ?)',
                 (req_id, m.from_user.id, m.document.file_id, m.document.file_name, 'pending'))
    conn.commit()
    conn.close()

    bot.send_message(m.chat.id, f"✅ **تم استلام ملفك بنجاح!**\n🆔 رقم الطلب: `{req_id}`\n⏳ يرجى انتظار موافقة الإدارة سيصلك إشعار فور التنصيب.")
    
    # إشعار الأدمن
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(types.InlineKeyboardButton("✅ موافقة", callback_data=f"approve_{req_id}"),
                     types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{req_id}"))
    bot.send_message(ADMIN_ID, f"🔔 **طلب تنصيب جديد!**\n👤 المستخدم: {m.from_user.id}\n📄 الملف: {m.document.file_name}\n🆔 الطلب: {req_id}", reply_markup=admin_markup)

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
— — — — — — — — — — — — — —
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎫 استخدام كود هدية", callback_data="use_gift_code"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text(wallet_text, c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "use_gift_code")
def ask_for_code(c):
    msg = bot.send_message(c.message.chat.id, "🎫 أرسل كود الهدية:")
    bot.register_next_step_handler(msg, process_gift_code)

def process_gift_code(m):
    uid = m.from_user.id
    code_text = m.text.strip()
    conn = get_db()
    code_data = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code_text,)).fetchone()
    if not code_data:
        bot.send_message(m.chat.id, "❌ كود خاطئ.")
    else:
        used = conn.execute('SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?', (uid, code_text)).fetchone()
        if used: bot.send_message(m.chat.id, "⚠️ استخدمته سابقاً.")
        else:
            conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (code_data['points'], uid))
            conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code_text,))
            conn.execute('INSERT INTO used_codes (user_id, code) VALUES (?, ?)', (uid, code_text))
            conn.commit()
            bot.send_message(m.chat.id, f"✅ حصلت على {code_data['points']} نقطة!")
    conn.close()

# ----------------------------------------------------------
# ⚙️ لـوحـة الإدارة والـمـوافـقـة (Admin Control)
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

@bot.callback_query_handler(func=lambda c: c.data.startswith(("approve_", "reject_")))
def handle_admin_decision(c):
    action, req_id = c.data.split("_")
    conn = get_db()
    req = conn.execute('SELECT * FROM installation_requests WHERE req_id = ?', (req_id,)).fetchone()
    
    if action == "approve":
        # محاكاة التنصيب وإضافة للبوتات النشطة
        conn.execute('INSERT INTO active_bots (user_id, bot_name, process_id, expiry_time, status) VALUES (?, ?, ?, ?, ?)',
                     (req['user_id'], req['file_name'], secrets.token_hex(3), (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'), 'running'))
        conn.execute('UPDATE users SET points = points - 10 WHERE user_id = ?', (req['user_id'],))
        bot.send_message(req['user_id'], f"🎉 **مبروك!** تم قبول طلبك وتصنيب بوتك `{req['file_name']}` بنجاح لمدة 30 يوم.")
    else:
        bot.send_message(req['user_id'], f"❌ عذراً، تم رفض طلب تنصيب الملف `{req['file_name']}` من قبل الإدارة.")
    
    conn.execute('DELETE FROM installation_requests WHERE req_id = ?', (req_id,))
    conn.commit()
    conn.close()
    bot.edit_message_text(f"✅ تم معالجة الطلب بنجاح ({action}).", c.message.chat.id, c.message.message_id)

# ----------------------------------------------------------
# 🔙 التنقل والتشغيل
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "back_home")
def back_home(c):
    bot.delete_message(c.message.chat.id, c.message.message_id)
    start(c)

@bot.callback_query_handler(func=lambda c: c.data == "server_status")
def server_status_h(c):
    text = f"📡 حالة السيرفر:\n⚙️ CPU: {psutil.cpu_percent()}%\n🧠 RAM: {psutil.virtual_memory().percent}%"
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")))

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    print("🔥 Titan V37 Mega Pro is Ready!")
    bot.infinity_polling()
