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
DB_PATH = 'titan_final_fixed.db'
FILES_DIR = 'hosted_scripts'

if not os.path.exists(FILES_DIR): os.makedirs(FILES_DIR)

# --- 🗄️ قاعدة البيانات ---
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 10, username TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, link_id TEXT UNIQUE, file_path TEXT, status TEXT, expiry TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_name TEXT, file_id TEXT, days INTEGER DEFAULT 1)')
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 🌐 خادم الويب ---
@app.route('/run/<link_id>')
def serve_file(link_id):
    conn = get_db()
    p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (link_id,)).fetchone()
    conn.close()
    if p:
        expiry = datetime.strptime(p['expiry'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expiry: return "❌ انتهى الرابط", 403
        with open(p['file_path'], 'r', encoding='utf-8') as f: return Response(f.read(), mimetype='text/plain')
    return "❌ غير موجود", 404

# --- 🏠 الكيبورد الرئيسي ---
def main_kb(uid, name, pts):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📤 تنصيب مشروع", callback_data="nav_ins"),
           types.InlineKeyboardButton("📂 مشاريعي", callback_data="nav_projs"))
    kb.add(types.InlineKeyboardButton("💳 المحفظة", callback_data="nav_wall"),
           types.InlineKeyboardButton("📡 حالة السيرفر", callback_data="nav_srv"))
    kb.add(types.InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}"),
           types.InlineKeyboardButton("📢 القناة", url=f"https://t.me/{DEVELOPER_CHANNEL[1:]}"))
    if uid == ADMIN_ID: kb.add(types.InlineKeyboardButton("⚙️ لوحة الإدارة", callback_data="nav_admin"))
    
    text = f"— — — — — — — — — — — — — —\n🎭 أهلاً بك في استضافة تايتان\n— — — — — — — — — — — — — —\n👤 الاسم: {name}\n💰 رصيدك: {pts} نقطة\n🆔 آيديك: {uid}\n— — — — — — — — — — — — — —\n💸 اليوم بـ 5 نقاط فقط!\n— — — — — — — — — — — — — —"
    return text, kb

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    if not user:
        conn.execute('INSERT INTO users (user_id, points, username) VALUES (?, ?, ?)', (uid, 10, m.from_user.first_name))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    txt, kb = main_kb(uid, m.from_user.first_name, user['points'])
    bot.send_message(m.chat.id, txt, reply_markup=kb)

# --- 🔗 معالج الأزرار (الربط الصحيح) ---
@bot.callback_query_handler(func=lambda c: True)
def router(c):
    uid, cid, mid = c.from_user.id, c.message.chat.id, c.message.message_id
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()

    # 1. مشاريعي
    if c.data == "nav_projs":
        projs = conn.execute('SELECT * FROM projects WHERE user_id = ?', (uid,)).fetchall()
        kb = types.InlineKeyboardMarkup(row_width=1)
        if not projs:
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("❌ لا تملك مشاريع.", cid, mid, reply_markup=kb)
        else:
            for p in projs: kb.add(types.InlineKeyboardButton(f"📄 {p['name']}", callback_data=f"v_{p['link_id']}"))
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("📂 مشاريعك الحالية:", cid, mid, reply_markup=kb)

    elif c.data.startswith("v_"):
        lid = c.data.split("_")[1]
        p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (lid,)).fetchone()
        txt = f"📄 ملف: `{p['name']}`\n⏳ ينتهي: {p['expiry']}\n🔗 الرابط: `{BASE_URL}/run/{p['link_id']}`"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="nav_projs"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    # 2. المحفظة
    elif c.data == "nav_wall":
        kb = types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("🎫 استخدام كود", callback_data="use_gift"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
        )
        bot.edit_message_text(f"💳 رصيدك الحالي: {user['points']} نقطة.", cid, mid, reply_markup=kb)

    # 3. السيرفر
    elif c.data == "nav_srv":
        txt = f"⚙️ CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    # 4. لوحة الإدارة
    elif c.data == "nav_admin" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton("📥 الطلبات", callback_data="adm_reqs"),
            types.InlineKeyboardButton("👥 النقاط", callback_data="adm_pts"),
            types.InlineKeyboardButton("🎫 كود", callback_data="adm_gen"),
            types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
        )
        bot.edit_message_text("⚙️ التحكم الكامل", cid, mid, reply_markup=kb)

    elif c.data == "adm_reqs":
        reqs = conn.execute('SELECT * FROM requests').fetchall()
        if not reqs: bot.answer_callback_query(c.id, "لا توجد طلبات.")
        for r in reqs:
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ قبول", callback_data=f"acc_{r['req_id']}"))
            bot.send_message(cid, f"🔔 طلب من: {r['user_id']}\n📅 المدة: {r['days']} يوم", reply_markup=kb)

    elif c.data == "adm_pts":
        msg = bot.send_message(cid, "ارسل (ID المستخدم) (النقاط):")
        bot.register_next_step_handler(msg, step_pts)

    elif c.data == "adm_gen":
        msg = bot.send_message(cid, "ارسل (النقاط) (عدد الاستخدام):")
        bot.register_next_step_handler(msg, step_gen)

    elif c.data == "adm_bc":
        msg = bot.send_message(cid, "ارسل رسالة الإذاعة:")
        bot.register_next_step_handler(msg, step_bc)

    elif c.data == "use_gift":
        msg = bot.send_message(cid, "ارسل الكود:")
        bot.register_next_step_handler(msg, step_use_gift)

    elif c.data == "nav_ins":
        msg = bot.send_message(cid, "📤 ارسل ملف .py:")
        bot.register_next_step_handler(msg, step_upload)

    elif c.data == "back_home":
        txt, kb = main_kb(uid, user['username'], user['points'])
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    elif c.data.startswith("days_"):
        _, days, rid = c.data.split("_")
        conn.execute('UPDATE requests SET days = ? WHERE req_id = ?', (int(days), rid))
        conn.commit()
        bot.edit_message_text(f"✅ تم تحديد {days} يوم. بانتظار الأدمن.", cid, mid)
        bot.send_message(ADMIN_ID, f"🔔 طلب جديد لـ {days} يوم من {uid}")

    elif c.data.startswith("acc_"):
        rid = c.data.split("_")[1]
        req = conn.execute('SELECT * FROM requests WHERE req_id = ?', (rid,)).fetchone()
        cost = req['days'] * 5
        lid = secrets.token_hex(4).upper()
        path = f"{FILES_DIR}/{lid}.py"
        with open(path, 'wb') as f: f.write(bot.download_file(bot.get_file(req['file_id']).file_path))
        exp = (datetime.now() + timedelta(days=req['days'])).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (cost, req['user_id']))
        conn.execute('INSERT INTO projects (user_id, name, link_id, file_path, status, expiry) VALUES (?, ?, ?, ?, ?, ?)', (req['user_id'], req['file_name'], lid, path, "مفعل", exp))
        conn.execute('DELETE FROM requests WHERE req_id = ?', (rid,))
        conn.commit()
        bot.send_message(req['user_id'], f"✅ تم التفعيل لـ {req['days']} يوم.")
        bot.delete_message(cid, mid)
    conn.close()

# --- وظائف الخطوات ---
def step_upload(m):
    if not m.document: return
    rid = secrets.token_hex(3).upper()
    conn = get_db(); conn.execute('INSERT INTO requests (req_id, user_id, file_name, file_id) VALUES (?, ?, ?, ?)', (rid, m.from_user.id, m.document.file_name, m.document.file_id)); conn.commit(); conn.close()
    kb = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("يوم (5)", callback_data=f"days_1_{rid}"),
        types.InlineKeyboardButton("أسبوع (35)", callback_data=f"days_7_{rid}"),
        types.InlineKeyboardButton("شهر (150)", callback_data=f"days_30_{rid}")
    )
    bot.send_message(m.chat.id, "🗓️ اختر المدة:", reply_markup=kb)

def step_pts(m):
    try:
        uid, pts = m.text.split()
        conn = get_db(); conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (int(pts), uid)); conn.commit(); conn.close()
        bot.send_message(m.chat.id, "✅ تم.")
    except: pass

def step_gen(m):
    try:
        pts, uses = m.text.split(); code = f"GIFT-{secrets.token_hex(3).upper()}"
        conn = get_db(); conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(pts), int(uses))); conn.commit(); conn.close()
        bot.send_message(m.chat.id, f"✅ الكود: `{code}`")
    except: pass

def step_bc(m):
    conn = get_db(); users = conn.execute('SELECT user_id FROM users').fetchall(); conn.close()
    for u in users:
        try: bot.send_message(u['user_id'], m.text)
        except: pass

def step_use_gift(m):
    conn = get_db(); code = m.text.strip()
    c = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code,)).fetchone()
    if c and c['current_uses'] < c['max_uses']:
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (c['points'], m.from_user.id))
        conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code,))
        conn.commit(); bot.send_message(m.chat.id, "✅ تم الشحن.")
    else: bot.send_message(m.chat.id, "❌ كود خطأ.")
    conn.close()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000)).start()
    bot.infinity_polling()
