# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـمـتـكـامـلـة (الـعـمـلاقة)
# 🛡️ نـظـام إدارة الاسـتـضـافـات الـمـحـلـيـة والـربـط الـخـارجي
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os, sys, time, sqlite3, secrets, psutil, telebot, uuid
from datetime import datetime, timedelta
from telebot import types

# ----------------------------------------------------------
# 🔑 الإعـدادات الـعـامـة
# ----------------------------------------------------------
BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'
SERVER_IP = "127.0.0.1" # ضع IP سيرفرك هنا للربط الخارجي

DB_PATH = 'titan_v37_ultimate.db'
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ----------------------------------------------------------
# 🗄️ تـهـيـئـة قـاعـدة الـبـيـانـات (نـظـام مـطـور)
# ----------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # المستخدمين
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER DEFAULT 5, join_date TEXT)')
    # طلبات التنصيب المعلقة
    c.execute('CREATE TABLE IF NOT EXISTS installation_requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_id TEXT, file_name TEXT, status TEXT DEFAULT "pending")')
    # المشاريع المنصبة (مع الرابط والمدة والحالة)
    c.execute('''CREATE TABLE IF NOT EXISTS active_bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        bot_name TEXT, 
        project_link TEXT,
        status TEXT DEFAULT "Active",
        start_date TEXT,
        expiry_date TEXT
    )''')
    # نظام الأكواد
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# ----------------------------------------------------------
# 🏠 الـواجـهـة الـرئـيـسـيـة
# ----------------------------------------------------------
def main_markup(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📤 تـنـصـيـب مـشـروع", callback_data="nav_install"),
        types.InlineKeyboardButton("📂 مـشـاريـعـي", callback_data="nav_my_projects"),
        types.InlineKeyboardButton("💳 الـمـحـفـظـة", callback_data="nav_wallet"),
        types.InlineKeyboardButton("📡 حـالـة الـسـيـرفـر", callback_data="nav_server")
    )
    markup.add(
        types.InlineKeyboardButton("👨‍💻 الـمـطـور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}"),
        types.InlineKeyboardButton("📢 الـقـنـاة", url=f"https://t.me/{DEVELOPER_CHANNEL[1:]}")
    )
    if uid == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("⚙️ لـوحـة الإدارة الـعـلـيـا", callback_data="nav_admin"))
    return markup

@bot.message_handler(commands=['start'])
def start_msg(m):
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
# 🔗 مـعـالـج الأزرار الـشـامـل (Full Callback Handler)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: True)
def handle_callbacks(c):
    uid, cid, mid = c.from_user.id, c.message.chat.id, c.message.message_id

    # --- 1. عرض المشاريع (مطور جداً) ---
    if c.data == "nav_my_projects":
        conn = get_db()
        projects = conn.execute('SELECT * FROM active_bots WHERE user_id = ?', (uid,)).fetchall()
        conn.close()
        
        if not projects:
            txt = "📂 **مـشـاريـعـي**\n\n❌ لا توجد لديك مشاريع منصبة حالياً."
        else:
            txt = "📂 **قائمة مشاريعك المنصبة:**\n\n"
            for p in projects:
                txt += f"🤖 **الاسم:** `{p['bot_name']}`\n"
                txt += f"🔗 **الرابط:** `{p['project_link']}`\n"
                txt += f"⏳ **المدة:** {p['expiry_date']}\n"
                txt += f"🟢 **الحالة:** {p['status']}\n"
                txt += "— — — — — — — — —\n"
        
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_home"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    # --- 2. تنصيب مشروع جديد ---
    elif c.data == "nav_install":
        msg = bot.send_message(cid, "📤 **يرجى إرسال ملف البوت الخاص بك (.py):**\nسيتم تنصيبه على سيرفرنا المحلي بعد الموافقة.")
        bot.register_next_step_handler(msg, process_upload)

    # --- 3. المحفظة (شحن + استخدام كود) ---
    elif c.data == "nav_wallet":
        conn = get_db()
        pts = conn.execute('SELECT points FROM users WHERE user_id = ?', (uid,)).fetchone()[0]
        conn.close()
        txt = f"💳 **الـمـحـفـظـة الـرقـمـيـة**\n\n💰 رصيدك الحالي: `{pts}` نقطة"
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("💳 شحن نقاط (تواصل مع المالك)", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}"),
            types.InlineKeyboardButton("🎫 استخدام كود شحن نقاط", callback_data="use_gift"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_home")
        )
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    # --- 4. حالة السيرفر (مع التحديث) ---
    elif c.data in ["nav_server", "update_stats"]:
        cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
        txt = f"📡 **حـالـة الـسـيـرفـر الـفـنـيـة**\n\n⚙️ CPU: `{cpu}%` \n🧠 RAM: `{ram}%` \n⏱️ الـوقـت: {datetime.now().strftime('%H:%M:%S')}"
        kb = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔄 تحديث البيانات", callback_data="update_stats"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_home")
        )
        try: bot.edit_message_text(txt, cid, mid, reply_markup=kb)
        except: bot.answer_callback_query(c.id, "✅ محدث")

    # --- 5. لوحة الإدارة ---
    elif c.data == "nav_admin" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📥 الطلبات", callback_data="adm_view_req"),
            types.InlineKeyboardButton("👥 المستخدمين", callback_data="adm_edit_users"),
            types.InlineKeyboardButton("📊 إحصائيات", callback_data="adm_global_stats"),
            types.InlineKeyboardButton("🎫 توليد كود", callback_data="adm_gen_code"),
            types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_home")
        )
        bot.edit_message_text("⚙️ **لوحة التحكم الإدارية**", cid, mid, reply_markup=kb)

    # --- 6. الرجوع للقائمة الرئيسية ---
    elif c.data == "back_to_home":
        conn = get_db()
        pts = conn.execute('SELECT points FROM users WHERE user_id = ?', (uid,)).fetchone()[0]
        conn.close()
        welcome = f"— — — — — — — — — — — — — —\n🎭 أهلاً بك في استضافة تايتان V37\n— — — — — — — — — — — — — —\n👤 الاسم: {c.from_user.first_name}\n💰 رصيدك الحالي: {pts} نقطة\n🆔 آيديك: {uid}\n— — — — — — — — — — — — — —"
        bot.edit_message_text(welcome, cid, mid, reply_markup=main_markup(uid))

    elif c.data == "use_gift":
        msg = bot.send_message(cid, "🎫 **أرسل كود الشحن الآن:**")
        bot.register_next_step_handler(msg, apply_code)

# ----------------------------------------------------------
# 📥 مـعـالـجـة الـمـلـفـات والـتـنـصـيـب
# ----------------------------------------------------------
def process_upload(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ خطأ: يرجى إرسال ملف بايثون فقط.")
        return
    
    req_id = secrets.token_hex(3).upper()
    conn = get_db()
    conn.execute('INSERT INTO installation_requests (req_id, user_id, file_id, file_name) VALUES (?, ?, ?, ?)',
                 (req_id, m.from_user.id, m.document.file_id, m.document.file_name))
    conn.commit()
    conn.close()
    
    bot.send_message(m.chat.id, f"✅ تم استلام ملفك! رقم الطلب: `{req_id}`\nسيتم مراجعته وتفعيله على السيرفر.")
    
    # إشعار الأدمن مع أزرار القبول
    adm_kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ قبول وتفعيل", callback_data=f"approve_{req_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{req_id}")
    )
    bot.send_message(ADMIN_ID, f"🔔 **طلب تنصيب جديد!**\n👤 الآيدي: {m.from_user.id}\n📄 الملف: {m.document.file_name}", reply_markup=adm_kb)

# ----------------------------------------------------------
# ⚙️ وظـائـف الإدارة (تـولـيد الأكـواد)
# ----------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data == "adm_gen_code")
def gen_code_step(c):
    msg = bot.send_message(c.message.chat.id, "🎫 أرسل (النقاط : عدد المستخدمين) مثال `50:10`:")
    bot.register_next_step_handler(msg, save_code)

def save_code(m):
    try:
        pts, limit = m.text.split(":")
        code = f"TITAN-{secrets.token_hex(3).upper()}"
        conn = get_db()
        conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(pts), int(limit)))
        conn.commit()
        conn.close()
        bot.send_message(m.chat.id, f"✅ تم التوليد:\n`{code}`\n💰 نقاط: {pts} | 👥 لـ {limit} أشخاص.")
    except: bot.send_message(m.chat.id, "❌ خطأ في التنسيق.")

def apply_code(m):
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
            bot.send_message(m.chat.id, f"✅ تم شحن {code['points']} نقطة!")
        else: bot.send_message(m.chat.id, "⚠️ استخدمت الكود سابقاً.")
    else: bot.send_message(m.chat.id, "❌ الكود غير صحيح أو منتهي.")
    conn.close()

# ----------------------------------------------------------
# 🏁 تـشـغـيـل
# ----------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Titan V37 Mega System Is Online...")
    bot.infinity_polling()
