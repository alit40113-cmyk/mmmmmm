# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـمـلـحـمـيـة الـشـامـلـة
# 💎 تـربـيـط كـامـل لـكـافـة الأزرار والـوظـائف بـدون نـقـص
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os, sqlite3, secrets, telebot, threading, psutil, time
from flask import Flask, Response, jsonify
from datetime import datetime, timedelta
from telebot import types

# --- ⚙️ الإعدادات ---
BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'
BASE_URL = "http://YOUR_SERVER_IP:5000" 

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)
DB_PATH = 'titan_v37_empire_fixed.db'
FILES_DIR = 'hosted_scripts'

if not os.path.exists(FILES_DIR): os.makedirs(FILES_DIR)

# --- 🗄️ نظام قاعدة البيانات ---
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 5, username TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, link_id TEXT UNIQUE, file_path TEXT, status TEXT, expiry TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_name TEXT, file_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 🌐 خادم الويب (رابط السورس كود المنفصل) ---
@app.route('/run/<link_id>')
def serve_file(link_id):
    conn = get_db()
    p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (link_id,)).fetchone()
    conn.close()
    if p:
        expiry = datetime.strptime(p['expiry'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expiry:
            return "❌ خطأ: انتهت مدة صلاحية الاستضافة.", 403
        with open(p['file_path'], 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='text/plain')
    return "❌ الرابط غير موجود.", 404

# --- 🏠 القائمة الرئيسية ---
def main_kb(uid, name, pts):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📤 تنصيب مشروع", callback_data="nav_ins"),
           types.InlineKeyboardButton("📂 مشاريعي", callback_data="nav_projs"))
    kb.add(types.InlineKeyboardButton("💳 المحفظة", callback_data="nav_wall"),
           types.InlineKeyboardButton("📡 حالة السيرفر", callback_data="nav_srv"))
    kb.add(types.InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}"),
           types.InlineKeyboardButton("📢 القناة", url=f"https://t.me/{DEVELOPER_CHANNEL[1:]}"))
    if uid == ADMIN_ID:
        kb.add(types.InlineKeyboardButton("⚙️ لوحة الإدارة", callback_data="nav_admin"))
    
    text = f"— — — — — — — — — — — — — —\n🎭 أهلاً بك في استضافة تايتان V37\n— — — — — — — — — — — — — —\n👤 الاسم: {name}\n💰 رصيدك الحالي: {pts} نقطة\n🆔 آيديك: {uid}\n— — — — — — — — — — — — — —\n⚠️ نظام التنصيب الآمن:\nارفع ملفك وسيتم تنصيبه بعد موافقة الإدارة.\n— — — — — — — — — — — — — —"
    return text, kb

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    if not user:
        conn.execute('INSERT INTO users (user_id, points, username) VALUES (?, ?, ?)', (uid, 5, m.from_user.first_name))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    txt, kb = main_kb(uid, m.from_user.first_name, user['points'])
    bot.send_message(m.chat.id, txt, reply_markup=kb)

# --- 🔗 معالج الأزرار الشامل (الربط الكامل) ---
@bot.callback_query_handler(func=lambda c: True)
def router(c):
    uid, cid, mid = c.from_user.id, c.message.chat.id, c.message.message_id
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()

    # --- 📂 مشاريعي ---
    if c.data == "nav_projs":
        projs = conn.execute('SELECT * FROM projects WHERE user_id = ?', (uid,)).fetchall()
        kb = types.InlineKeyboardMarkup(row_width=2)
        if not projs:
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("❌ ليس لديك مشاريع حالياً.", cid, mid, reply_markup=kb)
        else:
            for p in projs:
                kb.add(types.InlineKeyboardButton(f"📄 {p['name']}", callback_data=f"v_{p['link_id']}"))
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("📂 مشاريعك الحالية (اضغط لعرض البيانات):", cid, mid, reply_markup=kb)

    elif c.data.startswith("v_"):
        lid = c.data.split("_")[1]
        p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (lid,)).fetchone()
        txt = f"📄 ملف: `{p['name']}`\n🟢 الحالة: {p['status']}\n⏳ ينتهي: {p['expiry']}\n🔗 الرابط: `{BASE_URL}/run/{p['link_id']}`"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="nav_projs"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    # --- 💳 المحفظة ---
    elif c.data == "nav_wall":
        txt = f"💳 **المحفظة الرقمية**\n💰 رصيدك: `{user['points']}` نقطة"
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("💳 شحن نقاط (المالك)", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}"),
               types.InlineKeyboardButton("🎫 استخدام كود شحن", callback_data="use_gift_code"),
               types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    # --- 📡 حالة السيرفر ---
    elif c.data in ["nav_srv", "refresh_srv"]:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        txt = f"📡 **بيانات السيرفر الحالية:**\n⚙️ CPU: `{cpu}%` \n🧠 RAM: `{ram}%` \n⏱️ الـوقت: {datetime.now().strftime('%H:%M:%S')}"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 تحديث البيانات", callback_data="refresh_srv"),
                                              types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        try: bot.edit_message_text(txt, cid, mid, reply_markup=kb)
        except: bot.answer_callback_query(c.id, "✅ محدث")

    # --- ⚙️ لوحة الإدارة ---
    elif c.data == "nav_admin" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📥 الطلبات", callback_data="adm_reqs"),
               types.InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="adm_users"),
               types.InlineKeyboardButton("🎫 توليد كود", callback_data="adm_gen_code"),
               types.InlineKeyboardButton("📊 الإحصائيات", callback_data="adm_stats"),
               types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
               types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text("⚙️ **لوحة التحكم العليا**", cid, mid, reply_markup=kb)

    elif c.data == "adm_users":
        msg = bot.send_message(cid, "أرسل (ID المستخدم) ثم (النقاط) مثال: `8504553407 10` للإضافة أو `-10` للخصم:")
        bot.register_next_step_handler(msg, admin_edit_points)

    elif c.data == "adm_gen_code":
        msg = bot.send_message(cid, "أرسل (عدد النقاط) ثم (عدد الاستخدامات) مثال: `50 10`:")
        bot.register_next_step_handler(msg, admin_create_code)

    elif c.data == "adm_bc":
        msg = bot.send_message(cid, "أرسل رسالة الإذاعة الآن:")
        bot.register_next_step_handler(msg, admin_broadcast_msg)

    elif c.data == "use_gift_code":
        msg = bot.send_message(cid, "أرسل كود الشحن هنا:")
        bot.register_next_step_handler(msg, user_redeem_code)

    elif c.data == "back_home":
        txt, kb = main_kb(uid, user['username'], user['points'])
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    elif c.data == "nav_ins":
        msg = bot.send_message(cid, "📤 أرسل ملف الأداة رقم (1) بصيغة .py:")
        bot.register_next_step_handler(msg, handle_upload)

    elif c.data.startswith("acc_"):
        rid = c.data.split("_")[1]
        req = conn.execute('SELECT * FROM requests WHERE req_id = ?', (rid,)).fetchone()
        if req:
            lid = secrets.token_hex(4).upper()
            path = f"{FILES_DIR}/{lid}.py"
            with open(path, 'wb') as f: f.write(bot.download_file(bot.get_file(req['file_id']).file_path))
            exp = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
            conn.execute('INSERT INTO projects (user_id, name, link_id, file_path, status, expiry) VALUES (?, ?, ?, ?, ?, ?)', (req['user_id'], req['file_name'], lid, path, "مفعل 🟢", exp))
            conn.execute('DELETE FROM requests WHERE req_id = ?', (rid,))
            conn.commit()
            bot.send_message(req['user_id'], f"✅ تم تفعيل مشروعك بنجاح!\n🔗 الرابط: `{BASE_URL}/run/{lid}`")
            bot.delete_message(cid, mid)
    conn.close()

# --- وظائف الإدارة العميقة ---
def admin_edit_points(m):
    try:
        target_id, amount = m.text.split()
        conn = get_db()
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (int(amount), target_id))
        conn.commit(); conn.close()
        bot.send_message(m.chat.id, f"✅ تم تعديل نقاط المستخدم {target_id} بـ {amount}")
    except: bot.send_message(m.chat.id, "❌ خطأ في الإدخال.")

def admin_create_code(m):
    try:
        pts, uses = m.text.split()
        code = f"TITAN-{secrets.token_hex(3).upper()}"
        conn = get_db()
        conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(pts), int(uses)))
        conn.commit(); conn.close()
        bot.send_message(m.chat.id, f"✅ تم إنشاء كود:\n`{code}`\nيعطي {pts} نقطة لـ {uses} أشخاص.")
    except: bot.send_message(m.chat.id, "❌ فشل الإنشاء.")

def admin_broadcast_msg(m):
    conn = get_db()
    users = conn.execute('SELECT user_id FROM users').fetchall()
    conn.close()
    count = 0
    for u in users:
        try: bot.send_message(u['user_id'], m.text); count += 1
        except: pass
    bot.send_message(m.chat.id, f"✅ تم إرسال الإذاعة لـ {count} مستخدم.")

def user_redeem_code(m):
    code = m.text.strip()
    conn = get_db()
    c = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code,)).fetchone()
    used = conn.execute('SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?', (m.from_user.id, code)).fetchone()
    if c and not used and c['current_uses'] < c['max_uses']:
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (c['points'], m.from_user.id))
        conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code,))
        conn.execute('INSERT INTO used_codes (user_id, code) VALUES (?, ?)', (m.from_user.id, code))
        conn.commit()
        bot.send_message(m.chat.id, f"✅ تم شحن {c['points']} نقطة بنجاح!")
    else: bot.send_message(m.chat.id, "❌ الكود غير صحيح أو مستخدم مسبقاً.")
    conn.close()

def handle_upload(m):
    if not m.document: return
    rid = secrets.token_hex(3).upper()
    conn = get_db()
    conn.execute('INSERT INTO requests (req_id, user_id, file_name, file_id) VALUES (?, ?, ?, ?)', (rid, m.from_user.id, m.document.file_name, m.document.file_id))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, "✅ تم رفع الملف. بانتظار موافقة الإدارة.")
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ قبول", callback_data=f"acc_{rid}"))
    bot.send_message(ADMIN_ID, f"🔔 طلب جديد:\n👤 {m.from_user.id}\n📄 {m.document.file_name}", reply_markup=kb)

# --- التشغيل المتزامن ---
def run_api(): app.run(host='0.0.0.0', port=5000, threaded=True)
if __name__ == "__main__":
    threading.Thread(target=run_api).start()
    bot.infinity_polling()
