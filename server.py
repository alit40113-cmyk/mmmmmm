import os, sys, sqlite3, secrets, telebot, threading, psutil, time, subprocess, shutil, requests
from flask import Flask, Response, jsonify
from datetime import datetime, timedelta
from telebot import types

# --- [ الإعدادات ] ---
BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'
BASE_URL = "https://mmmmmm-production-14d7.up.railway.app"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)
DB_PATH = 'titan_v37_final.db'
FILES_DIR = 'hosted_scripts'

if not os.path.exists(FILES_DIR): os.makedirs(FILES_DIR)

# --- [ قاعدة البيانات ] ---
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 5, username TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, link_id TEXT UNIQUE, file_path TEXT, status TEXT, pid INTEGER, expiry TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_name TEXT, file_id TEXT, days INTEGER DEFAULT 1)')
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- [ خادم الويب ] ---
@app.route('/')
def health(): return "Titan Online", 200

@app.route('/run/<link_id>')
def serve_file(link_id):
    conn = get_db()
    p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (link_id,)).fetchone()
    conn.close()
    if p:
        if os.path.exists(p['file_path']):
            with open(p['file_path'], 'r', encoding='utf-8') as f:
                return Response(f.read(), mimetype='text/plain')
    return "❌ الرابط غير موجود.", 404

# --- [ القائمة الرئيسية ] ---
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
    
    text = f"— — — — — — — — — — — — — —\n🎭 أهلاً بك في استضافة تايتان V37\n— — — — — — — — — — — — — —\n👤 الاسم: {name}\n💰 رصيدك الحالي: {pts} نقطة\n🆔 آيديك: {uid}\n— — — — — — — — — — — — — —"
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

# --- [ 📤 دالة التنصيب الأصلية (بدون تغيير) ] ---
def handle_upload(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ أرسل ملف بايثون فقط.")
        return
    rid = secrets.token_hex(3).upper()
    conn = get_db()
    conn.execute('INSERT INTO requests (req_id, user_id, file_name, file_id) VALUES (?, ?, ?, ?)', (rid, m.from_user.id, m.document.file_name, m.document.file_id))
    conn.commit(); conn.close()
    kb = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("يوم (5ن)", callback_data=f"set_days_1_{rid}"),
        types.InlineKeyboardButton("أسبوع (35ن)", callback_data=f"set_days_7_{rid}"),
        types.InlineKeyboardButton("شهر (150ن)", callback_data=f"set_days_30_{rid}"))
    bot.send_message(m.chat.id, "🗓️ اختر مدة الاستضافة:", reply_markup=kb)

# --- [ 🔗 معالجة الأزرار والتربيط الكامل ] ---
@bot.callback_query_handler(func=lambda c: True)
def router(c):
    uid, cid, mid = c.from_user.id, c.message.chat.id, c.message.message_id
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()

    if c.data == "nav_ins":
        msg = bot.send_message(cid, "📤 أرسل ملف الأداة بصيغة .py:")
        bot.register_next_step_handler(msg, handle_upload)

    elif c.data == "nav_projs":
        projs = conn.execute('SELECT * FROM projects WHERE user_id = ?', (uid,)).fetchall()
        kb = types.InlineKeyboardMarkup(row_width=2)
        if not projs:
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("❌ ليس لديك مشاريع حالياً.", cid, mid, reply_markup=kb)
        else:
            for p in projs: kb.add(types.InlineKeyboardButton(f"📄 {p['name']}", callback_data=f"v_{p['link_id']}"))
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("📂 مشاريعك الحالية:", cid, mid, reply_markup=kb)

    elif c.data.startswith("v_"):
        lid = c.data.split("_")[1]
        p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (lid,)).fetchone()
        txt = f"📄 ملف: `{p['name']}`\n🟢 الحالة: {p['status']}\n⏳ ينتهي: {p['expiry']}\n🔗 الرابط: `{BASE_URL}/run/{lid}`"
        kb = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🗑️ حذف المشروع", callback_data=f"del_{lid}"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="nav_projs"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    elif c.data.startswith("del_"):
        lid = c.data.split("_")[1]
        conn.execute('DELETE FROM projects WHERE link_id = ?', (lid,))
        conn.commit()
        bot.answer_callback_query(c.id, "✅ تم حذف المشروع.")
        # العودة لقائمة المشاريع بعد الحذف
        projs = conn.execute('SELECT * FROM projects WHERE user_id = ?', (uid,)).fetchall()
        kb = types.InlineKeyboardMarkup(row_width=2)
        for p in projs: kb.add(types.InlineKeyboardButton(f"📄 {p['name']}", callback_data=f"v_{p['link_id']}"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text("📂 مشاريعك الحالية:", cid, mid, reply_markup=kb)

    elif c.data == "nav_wall":
        txt = f"💳 **المحفظة**\n💰 رصيدك: `{user['points']}` نقطة"
        kb = types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("💳 شحن نقاط (المالك)", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}"),
            types.InlineKeyboardButton("🎫 استخدام كود شحن", callback_data="use_gift_code"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    elif c.data == "nav_admin" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton("📥 الطلبات", callback_data="adm_reqs"),
            types.InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="adm_users"),
            types.InlineKeyboardButton("🎫 توليد كود", callback_data="adm_gen_code"),
            types.InlineKeyboardButton("📊 الإحصائيات", callback_data="adm_stats"),
            types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text("⚙️ لوحة الإدارة", cid, mid, reply_markup=kb)

    elif c.data == "adm_reqs":
        reqs = conn.execute('SELECT * FROM requests').fetchall()
        if not reqs: bot.answer_callback_query(c.id, "لا توجد طلبات.")
        for r in reqs:
            kb = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("✅ قبول", callback_data=f"acc_{r['req_id']}"),
                types.InlineKeyboardButton("❌ رفض", callback_data=f"rej_{r['req_id']}"))
            bot.send_message(cid, f"🔔 طلب من: `{r['user_id']}`\n📄 ملف: `{r['file_name']}`\n📅 مدة: {r['days']} يوم", reply_markup=kb)

    elif c.data == "adm_stats":
        u = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        p = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
        bot.answer_callback_query(c.id, f"👥 مستخدمين: {u}\n🚀 مشاريع: {p}", show_alert=True)

    elif c.data == "adm_bc":
        msg = bot.send_message(cid, "📢 أرسل رسالة الإذاعة:")
        bot.register_next_step_handler(msg, admin_broadcast_msg)

    elif c.data == "adm_users":
        msg = bot.send_message(cid, "👤 أرسل (آيدي مسافة نقاط):")
        bot.register_next_step_handler(msg, admin_edit_points)

    elif c.data == "adm_gen_code":
        msg = bot.send_message(cid, "🎫 أرسل (نقاط مسافة عدد):")
        bot.register_next_step_handler(msg, admin_create_code)

    elif c.data == "use_gift_code":
        msg = bot.send_message(cid, "🎫 أرسل كود الشحن:")
        bot.register_next_step_handler(msg, user_redeem_code)

    elif c.data.startswith("set_days_"):
        _, _, days, rid = c.data.split("_")
        conn.execute('UPDATE requests SET days = ? WHERE req_id = ?', (int(days), rid))
        conn.commit()
        bot.edit_message_text(f"✅ تم تحديد {days} يوم. طلبك بانتظار الإدارة.", cid, mid)

    elif c.data.startswith("acc_"):
        rid = c.data.split("_")[1]
        process_approval(rid, cid, mid)

    elif c.data == "back_home":
        txt, kb = main_kb(uid, user['username'], user['points'])
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    conn.close()

# --- [ الدوال البرمجية ] ---

def admin_broadcast_msg(m):
    conn = get_db(); users = conn.execute('SELECT user_id FROM users').fetchall(); conn.close()
    count = 0
    for u in users:
        try: bot.copy_message(u['user_id'], m.chat.id, m.message_id); count += 1
        except: pass
    bot.send_message(m.chat.id, f"✅ تم الإرسال لـ {count} مستخدم.")

def admin_edit_points(m):
    try:
        tid, amt = m.text.split(); conn = get_db()
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (int(amt), int(tid)))
        conn.commit(); conn.close()
        bot.send_message(m.chat.id, "✅ تم التعديل.")
    except: bot.send_message(m.chat.id, "❌ خطأ في الصيغة.")

def admin_create_code(m):
    try:
        pts, uses = m.text.split(); code = f"TITAN-{secrets.token_hex(3).upper()}"
        conn = get_db(); conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(pts), int(uses)))
        conn.commit(); conn.close()
        bot.send_message(m.chat.id, f"✅ كود جديد: `{code}`")
    except: bot.send_message(m.chat.id, "❌ خطأ.")

def user_redeem_code(m):
    code = m.text.strip(); conn = get_db()
    c = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code,)).fetchone()
    used = conn.execute('SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?', (m.from_user.id, code)).fetchone()
    if c and not used and c['current_uses'] < c['max_uses']:
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (c['points'], m.from_user.id))
        conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code,))
        conn.execute('INSERT INTO used_codes (user_id, code) VALUES (?, ?)', (m.from_user.id, code))
        conn.commit(); bot.send_message(m.chat.id, "✅ تم الشحن.")
    else: bot.send_message(m.chat.id, "❌ كود غير صالح.")
    conn.close()

def process_approval(rid, cid, mid):
    conn = get_db(); req = conn.execute('SELECT * FROM requests WHERE req_id = ?', (rid,)).fetchone()
    if req:
        cost = req['days'] * 5
        u_pts = conn.execute('SELECT points FROM users WHERE user_id = ?', (req['user_id'],)).fetchone()['points']
        if u_pts >= cost:
            lid = secrets.token_hex(4).upper(); final_path = os.path.join(FILES_DIR, f"{lid}.py")
            f_info = bot.get_file(req['file_id'])
            with open(final_path, 'wb') as f: f.write(bot.download_file(f_info.file_path))
            exp = (datetime.now() + timedelta(days=req['days'])).strftime('%Y-%m-%d %H:%M:%S')
            conn.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (cost, req['user_id']))
            conn.execute('INSERT INTO projects (user_id, name, link_id, file_path, status, expiry) VALUES (?, ?, ?, ?, ?, ?)', 
                         (req['user_id'], req['file_name'], lid, final_path, "مفعل 🟢", exp))
            conn.execute('DELETE FROM requests WHERE req_id = ?', (rid,)); conn.commit()
            bot.send_message(req['user_id'], f"✅ تم القبول!\n🔗 `{BASE_URL}/run/{lid}`")
            bot.edit_message_text("✅ تم القبول.", cid, mid)
        else: bot.send_message(cid, "❌ رصيد ناقص.")
    conn.close()

# --- [ تشغيل الـ Port ] ---
def run_api():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_api, daemon=True).start()
    bot.infinity_polling()
