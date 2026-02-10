# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـمـلـحـمـيـة الـشـامـلـة
# 💎 جـلـب الآيـبـي تـلـقـائـيـاً + تـشـغـيـل سـيـرفر (شوش)
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os, sys, sqlite3, secrets, telebot, threading, psutil, time, subprocess, shutil, requests
from flask import Flask, Response, jsonify
from datetime import datetime, timedelta
from telebot import types

# --- ⚙️ الإعدادات المركزية ---
BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
ADMIN_ID = 8504553407
DEVELOPER_USERNAME = '@Alikhalafm'
DEVELOPER_CHANNEL = '@teamofghost'

# 🌐 جلب آيبي السيرفر تلقائياً لجعل الروابط جاهزة 100%
try:
    SERVER_IP = requests.get('https://api.ipify.org', timeout=5).text
except:
    SERVER_IP = "127.0.0.1" 

BASE_URL = f"http://{SERVER_IP}:5000"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)
DB_PATH = 'titan_v37_empire.db'
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
    c.execute('CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, link_id TEXT UNIQUE, file_path TEXT, status TEXT, pid INTEGER, expiry TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_name TEXT, file_id TEXT, days INTEGER DEFAULT 1)')
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 🌐 خادم الويب (توفير السورس للأداة الثانية) ---
@app.route('/run/<link_id>')
def serve_file(link_id):
    conn = get_db()
    p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (link_id,)).fetchone()
    conn.close()
    if p:
        expiry = datetime.strptime(p['expiry'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expiry:
            return "❌ انتهت صلاحية هذا الرابط.", 403
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
    
    text = (f"— — — — — — — — — — — — — —\n"
            f"🎭 أهلاً بك في استضافة تايتان V37\n"
            f"— — — — — — — — — — — — — —\n"
            f"👤 الاسم: {name}\n"
            f"💰 رصيدك: {pts} نقطة\n"
            f"🆔 آيديك: {uid}\n"
            f"— — — — — — — — — — — — — —\n"
            f"💸 السعر: 5 نقاط لكل يوم استضافة.\n"
            f"— — — — — — — — — — — — — —")
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

# --- 🔗 معالج الأزرار والعمليات ---
@bot.callback_query_handler(func=lambda c: True)
def router(c):
    uid, cid, mid = c.from_user.id, c.message.chat.id, c.message.message_id
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()

    # [1] تنصيب مشروع
    if c.data == "nav_ins":
        msg = bot.send_message(cid, "📤 أرسل ملف الأداة (.py) الآن:")
        bot.register_next_step_handler(msg, handle_upload)

    # [2] مشاريعي
    elif c.data == "nav_projs":
        projs = conn.execute('SELECT * FROM projects WHERE user_id = ?', (uid,)).fetchall()
        kb = types.InlineKeyboardMarkup(row_width=1)
        if not projs:
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("❌ لا تملك مشاريع حالياً.", cid, mid, reply_markup=kb)
        else:
            for p in projs:
                kb.add(types.InlineKeyboardButton(f"📄 {p['name']}", callback_data=f"v_{p['link_id']}"))
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("📂 مشاريعك الحالية:", cid, mid, reply_markup=kb)

    # [3] عرض تفاصيل مشروع
    elif c.data.startswith("v_"):
        lid = c.data.split("_")[1]
        p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (lid,)).fetchone()
        ready_link = f"{BASE_URL}/run/{p['link_id']}"
        txt = f"📄 ملف: `{p['name']}`\n🟢 الحالة: {p['status']}\n⏳ ينتهي: {p['expiry']}\n\n🔗 الرابط الجاهز للأداة:\n`{ready_link}`"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="nav_projs"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    # [4] المحفظة
    elif c.data == "nav_wall":
        txt = f"💳 **المحفظة الرقمية**\n💰 رصيدك الحالي: `{user['points']}` نقطة"
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("🎫 استخدام كود هدية", callback_data="use_gift_code"),
               types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    # [5] حالة السيرفر
    elif c.data in ["nav_srv", "refresh_srv"]:
        cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
        txt = f"📡 **حالة السيرفر:**\n⚙️ المعالج: `{cpu}%` \n🧠 الرام: `{ram}%` \n⏱️ الوقت: {datetime.now().strftime('%H:%M')}"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_srv"),
                                              types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        try: bot.edit_message_text(txt, cid, mid, reply_markup=kb)
        except: pass

    # [6] لوحة الإدارة
    elif c.data == "nav_admin" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton("📥 الطلبات", callback_data="adm_reqs"),
            types.InlineKeyboardButton("🎫 توليد كود", callback_data="adm_gen_code"),
            types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
        )
        bot.edit_message_text("⚙️ لوحة تحكم الأدمن", cid, mid, reply_markup=kb)

    # [7] قبول الطلبات (منطق شوش الحقيقي)
    elif c.data.startswith("acc_"):
        rid = c.data.split("_")[1]
        req = conn.execute('SELECT * FROM requests WHERE req_id = ?', (rid,)).fetchone()
        if req:
            cost = req['days'] * 5
            u_data = conn.execute('SELECT points FROM users WHERE user_id = ?', (req['user_id'],)).fetchone()
            if u_data['points'] < cost:
                bot.send_message(cid, "❌ رصيد المستخدم لا يكفي.")
            else:
                lid = secrets.token_hex(4).upper()
                user_folder = os.path.join(FILES_DIR, str(req['user_id']))
                if not os.path.exists(user_folder): os.makedirs(user_folder)
                final_path = os.path.join(user_folder, f"{lid}.py")
                
                # حفظ وتشغيل
                f_info = bot.get_file(req['file_id'])
                with open(final_path, 'wb') as f: f.write(bot.download_file(f_info.file_path))
                
                proc = subprocess.Popen([sys.executable, final_path])
                exp = (datetime.now() + timedelta(days=req['days'])).strftime('%Y-%m-%d %H:%M:%S')
                
                conn.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (cost, req['user_id']))
                conn.execute('INSERT INTO projects (user_id, name, link_id, file_path, status, pid, expiry) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                             (req['user_id'], req['file_name'], lid, final_path, "مفعل 🟢", proc.pid, exp))
                conn.execute('DELETE FROM requests WHERE req_id = ?', (rid,))
                conn.commit()
                
                ready_link = f"{BASE_URL}/run/{lid}"
                bot.send_message(req['user_id'], f"✅ **تم قبول مشروعك بنجاح!**\n\n🔗 الرابط الجاهز للتشغيل:\n`{ready_link}`\n\n⏳ المدة: {req['days']} يوم.")
                bot.edit_message_text(f"✅ تم التفعيل بنجاح. PID: {proc.pid}", cid, mid)

    # [8] اختيار الأيام
    elif c.data.startswith("set_days_"):
        _, _, days, rid = c.data.split("_")
        conn.execute('UPDATE requests SET days = ? WHERE req_id = ?', (int(days), rid))
        conn.commit()
        bot.edit_message_text(f"✅ تم تحديد {days} يوم. طلبك الآن قيد المراجعة لدى الأدمن.", cid, mid)
        
        kb_adm = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(f"✅ قبول وخصم {int(days)*5}", callback_data=f"acc_{rid}"))
        bot.send_message(ADMIN_ID, f"🔔 طلب جديد من {uid}\n📄 الملف: (موجود بالطلبات)\n📅 المدة: {days} يوم", reply_markup=kb_adm)

    elif c.data == "back_home":
        txt, kb = main_kb(uid, user['username'], user['points'])
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    conn.close()

# --- 🛠️ وظائف الإدخال ---
def handle_upload(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ خطأ: أرسل ملف بايثون فقط.")
        return
    rid = secrets.token_hex(3).upper()
    conn = get_db()
    conn.execute('INSERT INTO requests (req_id, user_id, file_name, file_id) VALUES (?, ?, ?, ?)', 
                 (rid, m.from_user.id, m.document.file_name, m.document.file_id))
    conn.commit(); conn.close()
    
    kb = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("يوم (5ن)", callback_data=f"set_days_1_{rid}"),
        types.InlineKeyboardButton("أسبوع (35ن)", callback_data=f"set_days_7_{rid}"),
        types.InlineKeyboardButton("شهر (150ن)", callback_data=f"set_days_30_{rid}")
    )
    bot.send_message(m.chat.id, "🗓️ اختر مدة الاستضافة المطلوبة:", reply_markup=kb)

# --- التشغيل المتوازي (Flask + Bot) ---
def run_flask():
    app.run(host='0.0.0.0', port=5000, threaded=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print(f"📡 Titan Engine Started on {BASE_URL}")
    bot.infinity_polling()
