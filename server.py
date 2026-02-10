# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـشـامـلـة والـنـهـائـيـة
# 💎 نظام الربط المزدوج + تربيط كامل لجميع أزرار الإدارة
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os, sys, sqlite3, secrets, telebot, threading, psutil, time, subprocess, shutil, requests
from flask import Flask, Response, jsonify
from datetime import datetime, timedelta
from telebot import types

# --- ⚙️ الإعدادات المركزية ---
BOT_TOKEN = '8217773138:AAEcAKggoL2ES4mMi8HLLrU8CGb2Dy99MvY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'
BASE_URL = "https://mmmmmm-production-14d7.up.railway.app"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)
DB_PATH = 'titan_v37_final.db'
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
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 5, username TEXT, is_banned INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, link_id TEXT UNIQUE, file_path TEXT, status TEXT, pid INTEGER, expiry TEXT, is_raw INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_name TEXT, file_id TEXT, days INTEGER DEFAULT 1, is_raw INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 🌐 خادم الويب (رابط الأداة 2) ---
@app.route('/run/<link_id>')
def serve_file(link_id):
    conn = get_db()
    p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (link_id,)).fetchone()
    conn.close()
    if p:
        expiry = datetime.strptime(p['expiry'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expiry: return "❌ انتهت صلاحية الملف", 403
        if os.path.exists(p['file_path']):
            with open(p['file_path'], 'r', encoding='utf-8') as f:
                return Response(f.read(), mimetype='text/plain')
    return "❌ الملف غير موجود", 404

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
    
    text = f"— — — — — — — — — — — — — —\n🎭 أهلاً بك في استضافة تايتان V37\n— — — — — — — — — — — — — —\n👤 الاسم: {name}\n💰 رصيدك: {pts} نقطة\n🆔 آيديك: {uid}\n— — — — — — — — — — — — — —"
    return text, kb

# --- 📥 نظام التنصيب ---
def handle_upload(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ أرسل ملف بايثون (.py) فقط."); return
    rid = secrets.token_hex(3).upper()
    conn = get_db()
    conn.execute('INSERT INTO requests (req_id, user_id, file_name, file_id) VALUES (?, ?, ?, ?)', (rid, m.from_user.id, m.document.file_name, m.document.file_id))
    conn.commit(); conn.close()
    kb = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("يوم (5ن)", callback_data=f"set_days_1_{rid}"),
        types.InlineKeyboardButton("أسبوع (35ن)", callback_data=f"set_days_7_{rid}"),
        types.InlineKeyboardButton("شهر (150ن)", callback_data=f"set_days_30_{rid}")
    )
    bot.send_message(m.chat.id, "🗓️ اختر مدة الاستضافة:", reply_markup=kb)

# --- 🔗 معالج الأزرار الشامل ---
@bot.callback_query_handler(func=lambda c: True)
def router(c):
    uid, cid, mid = c.from_user.id, c.message.chat.id, c.message.message_id
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    
    if user and user['is_banned']:
        bot.answer_callback_query(c.id, "🚫 أنت محظور من استخدام البوت.", show_alert=True); return

    if c.data == "nav_ins":
        msg = bot.send_message(cid, "📤 أرسل ملف الأداة (.py) الآن:")
        bot.register_next_step_handler(msg, handle_upload)

    elif c.data.startswith("set_days_"):
        _, _, days, rid = c.data.split("_")
        conn.execute('UPDATE requests SET days = ? WHERE req_id = ?', (int(days), rid))
        conn.commit()
        kb = types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton("✅ نعم (أداة 2)", callback_data=f"link_yes_{rid}"),
            types.InlineKeyboardButton("❌ لا (استضافة)", callback_data=f"link_no_{rid}")
        )
        bot.edit_message_text("🔗 هل تريد ربط المشروع بالأداة رقم 2؟", cid, mid, reply_markup=kb)

    elif c.data.startswith("link_"):
        choice, rid = c.data.split("_")[1], c.data.split("_")[2]
        is_raw = 1 if choice == "yes" else 0
        conn.execute('UPDATE requests SET is_raw = ? WHERE req_id = ?', (is_raw, rid))
        conn.commit()
        bot.edit_message_text("✅ تم إرسال طلبك للإدارة. سيتم إشعارك عند القبول.", cid, mid)
        bot.send_message(ADMIN_ID, f"🔔 طلب جديد:\n🆔 `{rid}`\n👤 مستخدم: `{uid}`\n🛠 ربط أداة 2: {'نعم' if is_raw else 'لا'}")

    elif c.data == "nav_projs":
        projs = conn.execute('SELECT * FROM projects WHERE user_id = ?', (uid,)).fetchall()
        kb = types.InlineKeyboardMarkup(row_width=1)
        if not projs:
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("❌ ليس لديك مشاريع حالياً.", cid, mid, reply_markup=kb)
        else:
            for p in projs:
                kb.add(types.InlineKeyboardButton(f"📄 {p['name']}", callback_data=f"v_{p['link_id']}"))
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("📂 مشاريعك الحالية:", cid, mid, reply_markup=kb)

    elif c.data.startswith("v_"):
        lid = c.data.split("_")[1]
        p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (lid,)).fetchone()
        type_s = "أداة 2 🔗" if p['is_raw'] else "استضافة 🚀"
        txt = f"📄 ملف: `{p['name']}`\n🛠 النوع: {type_s}\n🟢 الحالة: {p['status']}\n⏳ ينتهي: {p['expiry']}\n🔗 الرابط: `{BASE_URL}/run/{p['link_id']}`"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="nav_projs"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    elif c.data == "nav_wall":
        txt = f"💳 **المحفظة**\n💰 رصيدك: `{user['points']}` نقطة"
        kb = types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("🎫 استخدام كود شحن", callback_data="use_gift_code"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
        )
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    elif c.data in ["nav_srv", "refresh_srv"]:
        cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
        txt = f"📡 **السيرفر:**\n⚙️ CPU: `{cpu}%` | 🧠 RAM: `{ram}%`"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_srv"),
                                              types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        try: bot.edit_message_text(txt, cid, mid, reply_markup=kb)
        except: pass

    # --- 🛠 لوحة الإدارة (تربيط كامل لجميع أزرارك) ---
    elif c.data == "nav_admin" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton("📥 الطلبات", callback_data="adm_reqs"),
            types.InlineKeyboardButton("📊 الإحصائيات", callback_data="adm_stats"),
            types.InlineKeyboardButton("➕ إضافة نقاط", callback_data="adm_add_pts"),
            types.InlineKeyboardButton("🎫 توليد كود", callback_data="adm_gen_code"),
            types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
            types.InlineKeyboardButton("🚫 حظر مستخدم", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔄 تصفير نقاط", callback_data="adm_reset"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
        )
        bot.edit_message_text("⚙️ **لوحة التحكم العليا**", cid, mid, reply_markup=kb)

    elif c.data == "adm_reqs":
        reqs = conn.execute('SELECT * FROM requests').fetchall()
        if not reqs: bot.answer_callback_query(c.id, "لا توجد طلبات.")
        for r in reqs:
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ قبول", callback_data=f"acc_{r['req_id']}"))
            bot.send_message(cid, f"📥 طلب: `{r['req_id']}`\n👤 مستخدم: `{r['user_id']}`\n🛠 أداة 2: {'نعم' if r['is_raw'] else 'لا'}", reply_markup=kb)

    elif c.data == "adm_stats":
        u_c = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        p_c = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
        bot.answer_callback_query(c.id, f"👥 مستخدمين: {u_c}\n🚀 مشاريع: {p_c}", show_alert=True)

    elif c.data == "adm_add_pts":
        msg = bot.send_message(cid, "👤 أرسل: (ID المستخدم) (النقاط)")
        bot.register_next_step_handler(msg, admin_add_points)

    elif c.data == "adm_bc":
        msg = bot.send_message(cid, "📢 أرسل رسالة الإذاعة:")
        bot.register_next_step_handler(msg, admin_broadcast)

    elif c.data == "adm_gen_code":
        msg = bot.send_message(cid, "🎫 أرسل: (النقاط) (عدد الاستخدامات)")
        bot.register_next_step_handler(msg, admin_gen_code)

    elif c.data == "adm_ban":
        msg = bot.send_message(cid, "🚫 أرسل ID المستخدم لحظر:")
        bot.register_next_step_handler(msg, admin_ban_user)

    elif c.data == "adm_reset":
        msg = bot.send_message(cid, "🔄 أرسل ID المستخدم لتصفير نقاطه:")
        bot.register_next_step_handler(msg, admin_reset_points)

    elif c.data.startswith("acc_"):
        rid = c.data.split("_")[1]
        req = conn.execute('SELECT * FROM requests WHERE req_id = ?', (rid,)).fetchone()
        if req:
            lid = secrets.token_hex(4).upper(); f_path = os.path.join(FILES_DIR, f"{lid}.py")
            f_info = bot.get_file(req['file_id'])
            with open(f_path, 'wb') as f: f.write(bot.download_file(f_info.file_path))
            
            pid = 0
            if req['is_raw'] == 0:
                try: proc = subprocess.Popen([sys.executable, f_path]); pid = proc.pid
                except: pass
            
            exp = (datetime.now() + timedelta(days=req['days'])).strftime('%Y-%m-%d %H:%M:%S')
            conn.execute('INSERT INTO projects (user_id, name, link_id, file_path, status, pid, expiry, is_raw) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                         (req['user_id'], req['file_name'], lid, f_path, "مفعل 🟢", pid, exp, req['is_raw']))
            conn.execute('DELETE FROM requests WHERE req_id = ?', (rid,))
            conn.commit()
            bot.send_message(req['user_id'], f"✅ تم تفعيل مشروعك!\n🔗 الرابط: `{BASE_URL}/run/{lid}`")
            bot.edit_message_text("✅ تمت الموافقة.", cid, mid)

    elif c.data == "use_gift_code":
        msg = bot.send_message(cid, "🎫 أرسل الكود:")
        bot.register_next_step_handler(msg, user_redeem)

    elif c.data == "back_home":
        txt, kb = main_kb(uid, user['username'], user['points'])
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    conn.close()

# --- 🛠️ دوال التنفيذ الإداري (كاملة ومربوطة) ---
def admin_broadcast(m):
    conn = get_db(); users = conn.execute('SELECT user_id FROM users').fetchall(); conn.close()
    for u in users:
        try: bot.send_message(u['user_id'], m.text)
        except: pass
    bot.send_message(m.chat.id, "✅ تم إرسال الإذاعة.")

def admin_add_points(m):
    try:
        tid, pts = m.text.split(); conn = get_db()
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (int(pts), tid))
        conn.commit(); conn.close(); bot.send_message(m.chat.id, "✅ تم إضافة النقاط.")
    except: bot.send_message(m.chat.id, "❌ خطأ بالصيغة.")

def admin_reset_points(m):
    conn = get_db(); conn.execute('UPDATE users SET points = 0 WHERE user_id = ?', (m.text,)); conn.commit(); conn.close()
    bot.send_message(m.chat.id, "✅ تم تصفير النقاط.")

def admin_gen_code(m):
    try:
        pts, uses = m.text.split(); code = f"TITAN-{secrets.token_hex(3).upper()}"
        conn = get_db(); conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(pts), int(uses)))
        conn.commit(); conn.close(); bot.send_message(m.chat.id, f"✅ كود: `{code}`")
    except: bot.send_message(m.chat.id, "❌ خطأ.")

def admin_ban_user(m):
    conn = get_db(); conn.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (m.text,)); conn.commit(); conn.close()
    bot.send_message(m.chat.id, "✅ تم الحظر.")

def user_redeem(m):
    code = m.text.strip(); conn = get_db()
    c = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code,)).fetchone()
    if c and c['current_uses'] < c['max_uses']:
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (c['points'], m.from_user.id))
        conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code,))
        conn.commit(); bot.send_message(m.chat.id, "✅ شحنت بنجاح.")
    else: bot.send_message(m.chat.id, "❌ كود خطأ.")
    conn.close()

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id; conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    if not user:
        conn.execute('INSERT INTO users (user_id, points, username) VALUES (?, 10, ?)', (uid, 10, m.from_user.first_name))
        conn.commit(); user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    txt, kb = main_kb(uid, m.from_user.first_name, user['points'])
    bot.send_message(m.chat.id, txt, reply_markup=kb); conn.close()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000))), daemon=True).start()
    bot.infinity_polling()

