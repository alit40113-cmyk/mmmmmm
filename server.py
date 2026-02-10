import os, sys, sqlite3, secrets, telebot, threading, psutil, subprocess, shutil
from flask import Flask, Response
from datetime import datetime, timedelta
from telebot import types

# --- ⚙️ الإعدادات المركزية ---
BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'
BASE_URL = "http://YOUR_SERVER_IP:5000" # استبدل YOUR_SERVER_IP بآيبي سيرفرك

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)
DB_PATH = 'titan_final_system.db'
FILES_DIR = 'hosted_projects'

if not os.path.exists(FILES_DIR): os.makedirs(FILES_DIR)

# --- 🗄️ نظام قاعدة البيانات ---
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 10, username TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, link_id TEXT UNIQUE, file_path TEXT, pid INTEGER, expiry TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_name TEXT, file_id TEXT, days INTEGER DEFAULT 1)')
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 🌐 خادم الويب (عرض السورس) ---
@app.route('/run/<link_id>')
def serve_file(link_id):
    conn = get_db()
    p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (link_id,)).fetchone()
    conn.close()
    if p:
        if datetime.now() > datetime.strptime(p['expiry'], '%Y-%m-%d %H:%M:%S'):
            return "❌ انتهت مدة الاستضافة.", 403
        with open(p['file_path'], 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='text/plain')
    return "❌ الرابط غير موجود.", 404

# --- 🏠 واجهة البوت ---
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
    
    text = f"— — — — — — — — — — — — — —\n🎭 أهلاً بك في استضافة تايتان V37\n— — — — — — — — — — — — — —\n👤 الاسم: {name}\n💰 رصيدك: {pts} نقطة\n🆔 آيديك: {uid}\n— — — — — — — — — — — — — —\n💸 السعر: 5 نقاط لكل يوم استضافة.\n— — — — — — — — — — — — — —"
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

# --- 🔗 معالجة العمليات (الأزرار) ---
@bot.callback_query_handler(func=lambda c: True)
def router(c):
    uid, cid, mid = c.from_user.id, c.message.chat.id, c.message.message_id
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()

    # 📤 تنصيب مشروع
    if c.data == "nav_ins":
        msg = bot.send_message(cid, "📤 أرسل ملف الـ .py الآن ليتم فحصه:")
        bot.register_next_step_handler(msg, handle_upload)

    # 🗓️ تحديد الأيام
    elif c.data.startswith("set_days_"):
        _, _, days, rid = c.data.split("_")
        conn.execute('UPDATE requests SET days = ? WHERE req_id = ?', (int(days), rid))
        conn.commit()
        bot.edit_message_text(f"✅ تم تحديد {days} يوم. سيتم إرسال طلبك للإدارة للموافقة.", cid, mid)
        # إشعار الأدمن
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(f"✅ قبول وخصم {int(days)*5}ن", callback_data=f"acc_{rid}"))
        bot.send_message(ADMIN_ID, f"🔔 طلب تنصيب جديد:\n👤 المستخدم: {uid}\n📅 المدة: {days} يوم", reply_markup=kb)

    # ✅ موافقة الأدمن (دالة شوش المدمجة)
    elif c.data.startswith("acc_"):
        rid = c.data.split("_")[1]
        req = conn.execute('SELECT * FROM requests WHERE req_id = ?', (rid,)).fetchone()
        if req:
            cost = req['days'] * 5
            if user['points'] < cost:
                bot.answer_callback_query(c.id, "❌ رصيد المستخدم غير كافٍ.", show_alert=True)
            else:
                lid = secrets.token_hex(4).upper()
                user_dir = os.path.join(FILES_DIR, str(req['user_id']))
                if not os.path.exists(user_dir): os.makedirs(user_dir)
                final_path = os.path.join(user_dir, f"{lid}.py")
                
                # حفظ وتشغيل (Logic شوش)
                file_info = bot.get_file(req['file_id'])
                with open(final_path, 'wb') as f: f.write(bot.download_file(file_info.file_path))
                
                # تشغيل كعملية خلفية
                proc = subprocess.Popen([sys.executable, final_path])
                exp = (datetime.now() + timedelta(days=req['days'])).strftime('%Y-%m-%d %H:%M:%S')
                
                conn.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (cost, req['user_id']))
                conn.execute('INSERT INTO projects (user_id, name, link_id, file_path, pid, expiry) VALUES (?, ?, ?, ?, ?, ?)', 
                             (req['user_id'], req['file_name'], lid, final_path, proc.pid, exp))
                conn.execute('DELETE FROM requests WHERE req_id = ?', (rid,))
                conn.commit()
                
                bot.send_message(req['user_id'], f"✅ تم تفعيل مشروعك!\n🔗 الرابط: `{BASE_URL}/run/{lid}`\n💰 الخصم: {cost} نقطة.")
                bot.edit_message_text(f"✅ تم قبول الطلب وتشغيل الملف (PID: {proc.pid})", cid, mid)

    # 📂 مشاريعي
    elif c.data == "nav_projs":
        projs = conn.execute('SELECT * FROM projects WHERE user_id = ?', (uid,)).fetchall()
        kb = types.InlineKeyboardMarkup(row_width=1)
        if not projs:
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("❌ لا تملك مشاريع نشطة.", cid, mid, reply_markup=kb)
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

    # 💳 المحفظة
    elif c.data == "nav_wall":
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎫 كود هدية", callback_data="use_gift"),
                                              types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text(f"💳 رصيدك: {user['points']} نقطة", cid, mid, reply_markup=kb)

    # ⚙️ لوحة الإدارة
    elif c.data == "nav_admin" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton("📥 الطلبات", callback_data="adm_reqs"),
            types.InlineKeyboardButton("👥 شحن", callback_data="adm_pts"),
            types.InlineKeyboardButton("🎫 توليد كود", callback_data="adm_gen"),
            types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
        )
        bot.edit_message_text("⚙️ لوحة الإدارة", cid, mid, reply_markup=kb)

    elif c.data == "back_home":
        txt, kb = main_kb(uid, user['username'], user['points'])
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    conn.close()

# --- وظائف الاستقبال ---
def handle_upload(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ يرجى إرسال ملف بصيغة .py فقط.")
        return
    rid = secrets.token_hex(3).upper()
    conn = get_db()
    conn.execute('INSERT INTO requests (req_id, user_id, file_name, file_id) VALUES (?, ?, ?, ?)', 
                 (rid, m.from_user.id, m.document.file_name, m.document.file_id))
    conn.commit(); conn.close()
    
    kb = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("يوم (5ن)", callback_data=f"set_days_1_{rid}"),
        types.InlineKeyboardButton("3 أيام (15ن)", callback_data=f"set_days_3_{rid}"),
        types.InlineKeyboardButton("أسبوع (35ن)", callback_data=f"set_days_7_{rid}"),
        types.InlineKeyboardButton("شهر (150ن)", callback_data=f"set_days_30_{rid}")
    )
    bot.send_message(m.chat.id, "🗓️ اختر مدة الاستضافة المطلوبة:", reply_markup=kb)

# --- وظائف الإدارة (شحن، إذاعة، كود) ---
def admin_add_pts(m):
    try:
        u, p = m.text.split(); conn = get_db()
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (int(p), u))
        conn.commit(); conn.close(); bot.send_message(m.chat.id, "✅ تم الشحن.")
    except: pass

def admin_gen_gift(m):
    try:
        p, u = m.text.split(); code = f"TITAN-{secrets.token_hex(3).upper()}"
        conn = get_db(); conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(p), int(u)))
        conn.commit(); conn.close(); bot.send_message(m.chat.id, f"✅ الكود: `{code}`")
    except: pass

# --- تشغيل النظام ---
def run_flask(): app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
