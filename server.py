# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - الـنـسـخـة الـمـلـحـمـيـة الـكـامـلـة
# 🛡️ نظام شوش.py المطور + تربيط شامل لجميع الأزرار
# 🔗 رابط مباشر للأداة 2 + نظام تصفير وحظر وإحصائيات
# 👨‍💻 المطور: @Alikhalafm | 📢 القناة: @teamofghost
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

# ✅ رابط Railway الخاص بك (يستخدم لربط الأداة 2)
BASE_URL = "https://mmmmmm-production-14d7.up.railway.app"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)
DB_PATH = 'titan_final_v37.db'
FILES_DIR = 'hosted_scripts'

if not os.path.exists(FILES_DIR): os.makedirs(FILES_DIR)

# --- 🗄️ نظام قاعدة البيانات المتكامل ---
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # مستخدمين
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 10, username TEXT, joined_at TEXT, is_banned INTEGER DEFAULT 0)')
    # مشاريع
    c.execute('CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, link_id TEXT UNIQUE, file_path TEXT, status TEXT, expiry TEXT)')
    # طلبات التنصيب
    c.execute('CREATE TABLE IF NOT EXISTS requests (req_id TEXT PRIMARY KEY, user_id INTEGER, file_name TEXT, file_id TEXT, days INTEGER DEFAULT 1)')
    # أكواد الهدية
    c.execute('CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
    # سجل استخدام الأكواد
    c.execute('CREATE TABLE IF NOT EXISTS used_codes (user_id INTEGER, code TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 🌐 خادم الويب (Raw Script Server) ---
@app.route('/raw/<link_id>')
def serve_raw_script(link_id):
    """الرابط الذي تطلبه الأداة رقم 2 للحصول على الكود مباشرة"""
    conn = get_db()
    p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (link_id,)).fetchone()
    conn.close()
    if p and os.path.exists(p['file_path']):
        # فحص الصلاحية
        exp = datetime.strptime(p['expiry'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > exp:
            return "❌ تنبيه: انتهت صلاحية هذا المشروع.", 403
        with open(p['file_path'], 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='text/plain')
    return "❌ خطأ: الرابط غير موجود.", 404

# --- 🏠 لوحات التحكم والأزرار ---
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
    
    text = f"🎭 **أهلاً بك في استضافة تايتان V37**\n\n👤 الاسم: {name}\n💰 رصيدك: `{pts}` نقطة\n🆔 آيديك: `{uid}`"
    return text, kb

# --- 📥 نظام التنصيب (منطق شوش.py) ---
def handle_upload(m):
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.send_message(m.chat.id, "❌ أرسل ملف بايثون (.py) فقط.")
        return
    
    rid = secrets.token_hex(3).upper()
    conn = get_db()
    conn.execute('INSERT INTO requests (req_id, user_id, file_name, file_id) VALUES (?, ?, ?, ?)', 
                 (rid, m.from_user.id, m.document.file_name, m.document.file_id))
    conn.commit(); conn.close()
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("يوم (5ن)", callback_data=f"set_days_1_{rid}"),
           types.InlineKeyboardButton("أسبوع (35ن)", callback_data=f"set_days_7_{rid}"),
           types.InlineKeyboardButton("شهر (150ن)", callback_data=f"set_days_30_{rid}"))
    bot.send_message(m.chat.id, "🗓️ اختر مدة الاستضافة المطلوبة للملف:", reply_markup=kb)

# --- 🔗 المعالج المركزي (كل الأزرار هنا) ---
@bot.callback_query_handler(func=lambda c: True)
def router(c):
    uid, cid, mid = c.from_user.id, c.message.chat.id, c.message.message_id
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()

    # 1. أوامر المستخدم العادي
    if c.data == "nav_ins":
        msg = bot.send_message(cid, "📤 أرسل ملف الأداة (.py) الآن:")
        bot.register_next_step_handler(msg, handle_upload)

    elif c.data == "nav_projs":
        projs = conn.execute('SELECT * FROM projects WHERE user_id = ?', (uid,)).fetchall()
        kb = types.InlineKeyboardMarkup(row_width=1)
        if not projs:
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("❌ لا يوجد لديك مشاريع نشطة حالياً.", cid, mid, reply_markup=kb)
        else:
            for p in projs:
                kb.add(types.InlineKeyboardButton(f"📄 {p['name']}", callback_data=f"view_{p['link_id']}"))
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
            bot.edit_message_text("📂 مشاريعك الحالية:", cid, mid, reply_markup=kb)

    elif c.data.startswith("view_"):
        lid = c.data.split("_")[1]
        p = conn.execute('SELECT * FROM projects WHERE link_id = ?', (lid,)).fetchone()
        txt = f"📄 **مشروع:** `{p['name']}`\n🟢 الحالة: {p['status']}\n⏳ ينتهي في: `{p['expiry']}`\n\n🔗 **رابط الربط للأداة الثانية:**\n`{BASE_URL}/raw/{lid}`"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="nav_projs"))
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    elif c.data == "nav_wall":
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎫 استخدام كود هدية", callback_data="redeem_code"),
                                              types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text(f"💳 **المحفظة الرقمية**\n\n💰 رصيدك الحالي: `{user['points']}` نقطة.", cid, mid, reply_markup=kb)

    elif c.data == "nav_srv":
        cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 تحديث", callback_data="nav_srv"),
                                              types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text(f"📡 **حالة السيرفر:**\n⚙️ المعالج: `{cpu}%`\n🧠 الذاكرة: `{ram}%`", cid, mid, reply_markup=kb)

    # 2. أوامر الإدارة (التربيط الكامل)
    elif c.data == "nav_admin" and uid == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📥 طلبات التنصيب", callback_data="adm_requests"),
               types.InlineKeyboardButton("👥 إدارة النقاط", callback_data="adm_points"))
        kb.add(types.InlineKeyboardButton("🎫 توليد كود", callback_data="adm_gen_code"),
               types.InlineKeyboardButton("📊 الإحصائيات", callback_data="adm_stats"))
        kb.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_broadcast"),
               types.InlineKeyboardButton("🚫 حظر مستخدم", callback_data="adm_ban"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text("⚙️ **لوحة التحكم العليا**", cid, mid, reply_markup=kb)

    elif c.data == "adm_requests":
        reqs = conn.execute('SELECT * FROM requests').fetchall()
        if not reqs: bot.answer_callback_query(c.id, "لا توجد طلبات معلقة.")
        for r in reqs:
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ قبول", callback_data=f"acc_{r['req_id']}"),
                                                  types.InlineKeyboardButton("❌ رفض", callback_data=f"rej_{r['req_id']}"))
            bot.send_message(cid, f"📥 طلب جديد!\n👤 من: `{r['user_id']}`\n📄 ملف: `{r['file_name']}`\n📅 مدة: `{r['days']}` يوم", reply_markup=kb)

    elif c.data == "adm_stats":
        u_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        p_count = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
        bot.answer_callback_query(c.id, f"👥 مستخدمين: {u_count}\n🚀 مشاريع نشطة: {p_count}", show_alert=True)

    # 3. معالجة طلبات التنصيب (الأيام)
    elif c.data.startswith("set_days_"):
        _, _, days, rid = c.data.split("_")
        conn.execute('UPDATE requests SET days = ? WHERE req_id = ?', (int(days), rid))
        conn.commit()
        bot.edit_message_text(f"✅ تم تحديد {days} يوم. طلبك قيد المراجعة الآن.", cid, mid)
        bot.send_message(ADMIN_ID, f"🔔 طلب تنصيب جديد برقم `{rid}` بانتظار الموافقة.")

    elif c.data.startswith("acc_"):
        rid = c.data.split("_")[1]
        req = conn.execute('SELECT * FROM requests WHERE req_id = ?', (rid,)).fetchone()
        if req:
            lid = secrets.token_hex(4).upper()
            f_path = os.path.join(FILES_DIR, f"{lid}.py")
            f_info = bot.get_file(req['file_id'])
            with open(f_path, 'wb') as f: f.write(bot.download_file(f_info.file_path))
            
            exp = (datetime.now() + timedelta(days=req['days'])).strftime('%Y-%m-%d %H:%M:%S')
            conn.execute('INSERT INTO projects (user_id, name, link_id, file_path, status, expiry) VALUES (?, ?, ?, ?, ?, ?)',
                         (req['user_id'], req['file_name'], lid, f_path, "مفعل 🟢", exp))
            conn.execute('DELETE FROM requests WHERE req_id = ?', (rid,))
            conn.commit()
            bot.send_message(req['user_id'], f"✅ تم تفعيل مشروعك!\n🔗 رابط الربط للأداة الثانية:\n`{BASE_URL}/raw/{lid}`")
            bot.edit_message_text("✅ تم قبول الطلب وتوليد الرابط.", cid, mid)

    # أزرار الإدخال (Step Handlers)
    elif c.data == "adm_points":
        msg = bot.send_message(cid, "أرسل: (الآيدي) (عدد النقاط)\nمثال: `8504553407 100`")
        bot.register_next_step_handler(msg, admin_add_pts)
    elif c.data == "adm_gen_code":
        msg = bot.send_message(cid, "أرسل: (النقاط) (عدد الاستخدامات)\nمثال: `50 10`")
        bot.register_next_step_handler(msg, admin_gen_code)
    elif c.data == "adm_broadcast":
        msg = bot.send_message(cid, "أرسل الرسالة التي تريد إذاعتها للجميع:")
        bot.register_next_step_handler(msg, admin_broadcast)
    elif c.data == "redeem_code":
        msg = bot.send_message(cid, "🎫 أرسل كود الهدية الآن:")
        bot.register_next_step_handler(msg, user_redeem)
    elif c.data == "back_home":
        txt, kb = main_kb(uid, user['username'], user['points'])
        bot.edit_message_text(txt, cid, mid, reply_markup=kb)

    conn.close()

# --- 🛠️ الوظائف التنفيذية ---
def admin_add_pts(m):
    try:
        target, pts = m.text.split(); conn = get_db()
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (int(pts), target))
        conn.commit(); conn.close(); bot.send_message(m.chat.id, "✅ تم إضافة النقاط بنجاح.")
    except: bot.send_message(m.chat.id, "❌ خطأ في الصيغة.")

def admin_gen_code(m):
    try:
        pts, uses = m.text.split(); code = f"TITAN-{secrets.token_hex(3).upper()}"
        conn = get_db(); conn.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code, int(pts), int(uses)))
        conn.commit(); conn.close(); bot.send_message(m.chat.id, f"✅ كود جديد: `{code}`\nيعطي `{pts}` نقطة لـ `{uses}` أشخاص.")
    except: bot.send_message(m.chat.id, "❌ فشل توليد الكود.")

def admin_broadcast(m):
    conn = get_db(); users = conn.execute('SELECT user_id FROM users').fetchall(); conn.close()
    count = 0
    for u in users:
        try: bot.send_message(u['user_id'], m.text); count += 1
        except: pass
    bot.send_message(m.chat.id, f"✅ تم الإرسال لـ {count} مستخدم.")

def user_redeem(m):
    code = m.text.strip(); conn = get_db()
    c = conn.execute('SELECT * FROM gift_codes WHERE code = ?', (code,)).fetchone()
    used = conn.execute('SELECT 1 FROM used_codes WHERE user_id = ? AND code = ?', (m.from_user.id, code)).fetchone()
    if c and not used and c['current_uses'] < c['max_uses']:
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (c['points'], m.from_user.id))
        conn.execute('UPDATE gift_codes SET current_uses = current_uses + 1 WHERE code = ?', (code,))
        conn.execute('INSERT INTO used_codes (user_id, code) VALUES (?, ?)', (m.from_user.id, code))
        conn.commit(); bot.send_message(m.chat.id, f"✅ تم شحن {c['points']} نقطة!")
    else: bot.send_message(m.chat.id, "❌ الكود غير صالح أو استخدمته سابقاً.")
    conn.close()

# --- 🚀 التشغيل النهائي ---
@bot.message_handler(commands=['start'])
def start(m):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (m.from_user.id,)).fetchone()
    if not user:
        conn.execute('INSERT INTO users (user_id, points, username, joined_at) VALUES (?, 10, ?, ?)', 
                     (m.from_user.id, m.from_user.first_name, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (m.from_user.id,)).fetchone()
    
    txt, kb = main_kb(m.from_user.id, m.from_user.first_name, user['points'])
    bot.send_message(m.chat.id, txt, reply_markup=kb)
    conn.close()

if __name__ == "__main__":
    # تشغيل Flask للسحب الخارجي
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000))), daemon=True).start()
    bot.infinity_polling()
