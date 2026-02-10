# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـمـتـكـامـلـة (الـعـمـلاقة)
# 🛡️ نـظـام إدارة الاسـتـضـافـات - بـدون أي اخـتـصـارات
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os, sys, time, sqlite3, logging, secrets, psutil, telebot
from datetime import datetime, timedelta
from telebot import types

# ----------------------------------------------------------
# 🔑 الإعـدادات والـثـوابـت
# ----------------------------------------------------------
BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'

DB_PATH = 'titan_final_v37.db'
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ----------------------------------------------------------
# 🗄️ قـاعـدة الـبـيـانـات الـشـامـلـة
# ----------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER DEFAULT 5, join_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS installation_requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_id TEXT, file_name TEXT, status TEXT DEFAULT "pending")')
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS active_bots (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, bot_name TEXT, expiry TEXT)')
    conn.commit()
    conn.close()

init_db()

# ----------------------------------------------------------
# 🏠 الـقـائمة الـرئـيسـية
# ----------------------------------------------------------
def main_markup(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📤 تـنـصـيـب مـشـروع", callback_data="install_proj"),
        types.InlineKeyboardButton("📂 مـشـاريـعـي", callback_data="my_projects"),
        types.InlineKeyboardButton("💳 الـمـحـفـظـة", callback_data="wallet_home"),
        types.InlineKeyboardButton("📡 حـالـة الـسـيـرفـر", callback_data="server_status")
    )
    markup.add(
        types.InlineKeyboardButton("👨‍💻 الـمـطـور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}"),
        types.InlineKeyboardButton("📢 الـقـنـاة", url=f"https://t.me/{DEVELOPER_CHANNEL[1:]}")
    )
    if uid == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("⚙️ لـوحـة الإدارة الـعـلـيـا", callback_data="admin_panel"))
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    if not user:
        conn.execute('INSERT INTO users (user_id, username, join_date) VALUES (?, ?, ?)', 
                     (uid, m.from_user.username, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    conn.close()

    welcome = f"""
— — — — — — — — — — — — — —
🎭 أهلاً بك في استضافة تايتان V37
— — — — — — — — — — — — — —
👤 الاسم: {m.from_user.first_name}
💰 رصيدك الحالي: {user['points']} نقطة
🆔 آيديك: {uid}
— — — — — — — — — — — — — —
⚠️ نظام التنصيب الآمن:
ارفع ملفك وسيتم تنصيبه بعد موافقة الإدارة.
— — — — — — — — — — — — — —
    """
    bot.send_message(m.chat.id, welcome, reply_markup=main_markup(uid))

# ----------------------------------------------------------
# 💳 1. الـمـحـفـظـة (شـحـن + أكـواد)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "wallet_home")
def wallet_home(c):
    conn = get_db()
    pts = conn.execute('SELECT points FROM users WHERE user_id = ?', (c.from_user.id,)).fetchone()[0]
    conn.close()
    
    text = f"💳 **مـحـفـظـتـك الـرقمـيـة**\n\n💰 رصيدك الحالي: `{pts}` نقطة"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💳 شحن نقاط (تواصل مع المالك)", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}"),
        types.InlineKeyboardButton("🎫 استخدام كود شحن", callback_data="use_code"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_home")
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "use_code")
def use_code(c):
    msg = bot.send_message(c.message.chat.id, "🎫 **أرسل كود الشحن الآن:**")
    bot.register_next_step_handler(msg, process_gift_code)

def process_gift_code(m):
    uid, code_txt = m.from_user.id, m.text.strip()
    conn = get_db()
    code = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code_txt,)).fetchone()
    if code and code['current_uses'] < code['max_uses']:
        used = conn.execute('SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?', (uid, code_txt)).fetchone()
        if not used:
            conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (code['points'], uid))
            conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code_txt,))
            conn.execute('INSERT INTO used_codes (user_id, code) VALUES (?, ?)', (uid, code_txt))
            conn.commit()
            bot.send_message(m.chat.id, f"✅ تم الشحن! حصلت على {code['points']} نقطة.")
        else: bot.send_message(m.chat.id, "❌ استخدمت هذا الكود مسبقاً.")
    else: bot.send_message(m.chat.id, "❌ الكود غير صحيح أو منتهي.")
    conn.close()

# ----------------------------------------------------------
# 📡 2. حـالـة الـسـيـرفـر (مـع زر الـتـحـديـث)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data in ["server_status", "refresh_status"])
def server_status(c):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    text = f"📡 **حـالـة الـسـيـرفـر الـفـنـيـة**\n\n⚙️ استهلاك المعالج: `{cpu}%` \n🧠 استهلاك الرام: `{ram}%` \n🗄️ استهلاك القرص: `{disk}%` \n⏱️ الوقت: {datetime.now().strftime('%H:%M:%S')}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 تحديث البيانات", callback_data="refresh_status"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_home"))
    
    # تجنب إرسال نفس المحتوى إذا لم تتغير البيانات
    try: bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    except: bot.answer_callback_query(c.id, "تم التحديث ✅")

# ----------------------------------------------------------
# ⚙️ 3. لـوحـة الإدارة الـعـلـيـا (الـمـتـكـامـلـة)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_panel(c):
    if c.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📥 الطلبات المعلقة", callback_data="adm_requests"),
        types.InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="adm_users"),
        types.InlineKeyboardButton("📊 إحصائيات البوت", callback_data="adm_stats_bot"),
        types.InlineKeyboardButton("🛰️ إحصائيات السيرفر", callback_data="server_status"),
        types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("🎫 توليد كود", callback_data="adm_gen_code")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_home"))
    bot.edit_message_text("⚙️ **لوحة التحكم الإدارية**\nاختر من الخيارات التالية:", c.message.chat.id, c.message.message_id, reply_markup=markup)

# إدارة المستخدمين (إضافة/خصم نقاط)
@bot.callback_query_handler(func=lambda c: c.data == "adm_users")
def adm_users(c):
    msg = bot.send_message(c.message.chat.id, "👤 أرسل آيدي المستخدم ثم القيمة (مثال: `8504553407 50` للزيادة أو `-50` للخصم):")
    bot.register_next_step_handler(msg, process_pts_change)

def process_pts_change(m):
    try:
        uid, val = m.text.split()
        conn = get_db()
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (int(val), int(uid)))
        conn.commit()
        conn.close()
        bot.send_message(m.chat.id, f"✅ تم تعديل رصيد {uid} بمقدار {val}.")
    except: bot.send_message(m.chat.id, "❌ خطأ في الصيغة.")

# توليد كود (نقاط + عدد مستخدمين)
@bot.callback_query_handler(func=lambda c: c.data == "adm_gen_code")
def adm_gen_code(c):
    msg = bot.send_message(c.message.chat.id, "🎫 أرسل (النقاط:عدد المستخدمين) مثال `100:5`:")
    bot.register_next_step_handler(msg, finalize_gen_code)

def finalize_gen_code(m):
    try:
        pts, limit = m.text.split(":")
        code = f"TITAN-{secrets.token_hex(3).upper()}"
        conn = get_db()
        conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(pts), int(limit)))
        conn.commit()
        conn.close()
        bot.send_message(m.chat.id, f"✅ تم إنشاء كود:\n`{code}`\n💰 النقاط: {pts}\n👥 الاستخدامات: {limit}")
    except: bot.send_message(m.chat.id, "❌ خطأ في التنسيق.")

# إدارة الطلبات المعلقة
@bot.callback_query_handler(func=lambda c: c.data == "adm_requests")
def adm_requests(c):
    conn = get_db()
    reqs = conn.execute('SELECT * FROM installation_requests WHERE status = "pending"').fetchall()
    conn.close()
    if not reqs:
        bot.answer_callback_query(c.id, "📭 لا توجد طلبات معلقة حالياً.", show_alert=True)
        return
    for r in reqs:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ قبول", callback_data=f"accept_{r['req_id']}"),
               types.InlineKeyboardButton("❌ رفض", callback_data=f"deny_{r['req_id']}"))
        bot.send_message(c.message.chat.id, f"⏳ طلب معلق:\n👤 المستخدم: {r['user_id']}\n📄 الملف: {r['file_name']}", reply_markup=kb)

# إحصائيات البوت
@bot.callback_query_handler(func=lambda c: c.data == "adm_stats_bot")
def adm_stats_bot(c):
    conn = get_db()
    u_count = conn.execute('SELECT count(*) FROM users').fetchone()[0]
    b_count = conn.execute('SELECT count(*) FROM active_bots').fetchone()[0]
    conn.close()
    bot.answer_callback_query(c.id, f"📊 إحصائيات:\n👥 مستخدمين: {u_count}\n🤖 بوتات نشطة: {b_count}", show_alert=True)

# الإذاعة العامة
@bot.callback_query_handler(func=lambda c: c.data == "adm_broadcast")
def adm_bc(c):
    msg = bot.send_message(c.message.chat.id, "📢 أرسل الرسالة التي تريد إذاعتها لجميع المستخدمين:")
    bot.register_next_step_handler(msg, start_broadcast)

def start_broadcast(m):
    conn = get_db()
    users = conn.execute('SELECT user_id FROM users').fetchall()
    conn.close()
    count = 0
    for u in users:
        try:
            bot.send_message(u['user_id'], m.text)
            count += 1
        except: pass
    bot.send_message(m.chat.id, f"✅ تمت الإذاعة لـ {count} مستخدم.")

# ----------------------------------------------------------
# 🔙 دوال الـتـنـقـل والـرجـوع
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "back_to_home")
def back_home(c):
    uid = c.from_user.id
    conn = get_db()
    user = conn.execute('SELECT points FROM users WHERE user_id = ?', (uid,)).fetchone()
    conn.close()
    welcome = f"""
— — — — — — — — — — — — — —
🎭 أهلاً بك في استضافة تايتان V37
— — — — — — — — — — — — — —
👤 الاسم: {c.from_user.first_name}
💰 رصيدك الحالي: {user['points']} نقطة
🆔 آيديك: {uid}
— — — — — — — — — — — — — —
⚠️ نظام التنصيب الآمن:
ارفع ملفك وسيتم تنصيبه بعد موافقة الإدارة.
— — — — — — — — — — — — — —
    """
    bot.edit_message_text(welcome, c.message.chat.id, c.message.message_id, reply_markup=main_markup(uid))

# ----------------------------------------------------------
# 🏁 تـشـغـيـل الـنـظـام
# ----------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Titan V37 Mega System is running...")
    bot.infinity_polling()
