# ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - نـظـام بـلاك تـيـك الـمـطـور
# 🛡️ نـظـام الـتـنـصـيـب بـعـد مـوافـقـة الأدمن (ضـد الـثـغـرات)
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os
import sys
import time
import json
import sqlite3
import logging
import hashlib
import secrets
import requests
import threading
import subprocess
import platform
import psutil
import re
import tempfile
import shutil
from io import BytesIO
from datetime import datetime, timedelta
from collections import defaultdict
import telebot
from telebot import types

# ----------------------------------------------------------
# 🔑 إعـدادات الـنـظـام الـمـركـزيـة
# ----------------------------------------------------------

BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'

ADMIN_ID = 8504553407

DEVELOPER_USERNAME = '@Alikhalafm'

DEVELOPER_CHANNEL = '@teamofghost'

UPLOAD_FOLDER = 'hosted_bots_data'

PENDING_FOLDER = 'waiting_area'

DB_PATH = 'titan_v37.db'

# 🤖 تهيئة البوت
bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------------
# 📁 تـهـيـئـة الـمـجـلـدات والـبـيـئـة
# ----------------------------------------------------------

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(PENDING_FOLDER):
    os.makedirs(PENDING_FOLDER)

# ----------------------------------------------------------
# 🛠️ إدارة قـاعـدة الـبـيـانـات (SQLite3)
# ----------------------------------------------------------

def get_db_connection():
    """إنشاء اتصال آمن مع قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """تأسيس الجداول اللازمة للنظام"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # جدول المستخدمين الأساسي
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            username TEXT, 
            points INTEGER DEFAULT 5, 
            join_date TEXT, 
            is_banned INTEGER DEFAULT 0
        )
    ''')
    
    # جدول البوتات التي تم تنصيبها وتعمل حالياً
    c.execute('''
        CREATE TABLE IF NOT EXISTS active_bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER, 
            bot_name TEXT, 
            file_path TEXT, 
            process_id INTEGER, 
            expiry_time TEXT, 
            status TEXT
        )
    ''')
    
    # جدول طلبات التنصيب التي تنتظر مراجعة الأدمن (سد الثغرة)
    c.execute('''
        CREATE TABLE IF NOT EXISTS installation_requests (
            req_id TEXT PRIMARY KEY, 
            user_id INTEGER, 
            file_name TEXT, 
            temp_path TEXT, 
            days INTEGER, 
            cost INTEGER,
            request_time TEXT
        )
    ''')
    
    # جدول أكواد الهدايا
    c.execute('''
        CREATE TABLE IF NOT EXISTS gift_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            code TEXT, 
            points INTEGER, 
            status TEXT DEFAULT 'unused'
        )
    ''')

    conn.commit()
    conn.close()

# تشغيل قاعدة البيانات عند الإقلاع
init_db()

# ----------------------------------------------------------
# 👤 وظـائـف الـمـسـتـخـدمـيـن والـنـقـاط
# ----------------------------------------------------------

def get_user(uid):
    """جلب بيانات المستخدم"""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    conn.close()
    return user

def register_user(uid, username):
    """تسجيل مستخدم جديد في النظام"""
    if not get_user(uid):
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (user_id, username, join_date) VALUES (?, ?, ?)',
            (uid, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        conn.close()

def get_points(uid):
    """التحقق من نقاط المستخدم"""
    u = get_user(uid)
    if u:
        return u['points']
    return 0

def update_points(uid, amount):
    """تحديث رصيد النقاط (زيادة أو نقصان)"""
    conn = get_db_connection()
    conn.execute(
        'UPDATE users SET points = points + ? WHERE user_id = ?',
        (amount, uid)
    )
    conn.commit()
    conn.close()

# ----------------------------------------------------------
# 🎨 واجـهـة بـلاك تـيـك الـرئـيـسـيـة
# ----------------------------------------------------------

@bot.message_handler(commands=['start'])
def start_command_handler(m):
    """الترحيب وعرض القائمة الرئيسية - تم التعديل لإضافة زر مشاريعي"""
    uid = m.from_user.id
    username = m.from_user.username
    
    # تسجيل المستخدم تلقائياً
    register_user(uid, username)
    
    # جلب الرصيد المحدث
    current_points = get_points(uid)
    
    welcome_text = f"""
*— — — — — — — — — — — — — —*
*🎭 أهلاً بك في استضافة تايتان V37*
*— — — — — — — — — — — — — —*
*👤 الاسم:* {m.from_user.first_name}
*💰 رصيدك الحالي:* `{current_points}` *نقطة*
*🆔 آيديك:* `{uid}`
*— — — — — — — — — — — — — —*
*⚠️ نظام التنصيب الآمن:*
*ارفع ملفك وسيتم تنصيبه بعد موافقة الإدارة.*
*— — — — — — — — — — — — — —*
    """
    
    # إنشاء الأزرار بتنسيق بلاك تيك المطور
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_install = types.InlineKeyboardButton("📤 تـنـصـيـب بـوت جـديـد", callback_data="start_install")
    # هذا هو زر "مشاريعي" المطلوب (الشغلة الثانية)
    btn_my_bots = types.InlineKeyboardButton("📂 مـشـاريـعـي", callback_data="my_active_bots") 
    
    btn_wallet = types.InlineKeyboardButton("💳 الـمـحـفـظـة", callback_data="wallet_info")
    btn_status = types.InlineKeyboardButton("📡 حـالـة الـسـيـرفـر", callback_data="server_health")
    
    btn_dev = types.InlineKeyboardButton("👨‍💻 الـمـطـور", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@','')}")
    btn_chan = types.InlineKeyboardButton("📢 الـقـنـاة", url=f"https://t.me/{DEVELOPER_CHANNEL.replace('@','')}")
    
    # إضافة الأزرار حسب الطلب
    markup.add(btn_install, btn_my_bots)
    markup.add(btn_wallet, btn_status)
    markup.add(btn_dev, btn_chan)
    
    # إضافة زر لوحة الإدارة للأدمن فقط
    if uid == ADMIN_ID:
        admin_btn = types.InlineKeyboardButton("⚙️ لـوحـة الإدارة", callback_data="admin_panel")
        markup.add(admin_btn)
        
    bot.send_message(
        m.chat.id, 
        welcome_text, 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# 📂 نـظـام إدارة مـشـاريـعـي والـرواـبـط (إضافة جديدة)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "my_active_bots")
def list_user_projects(c):
    """عرض قائمة المشاريع النشطة للمستخدم"""
    uid = c.from_user.id
    conn = get_db_connection()
    # جلب كافة المشاريع النشطة للمستخدم
    projects = conn.execute('SELECT * FROM active_bots WHERE user_id = ?', (uid,)).fetchall()
    conn.close()

    if not projects:
        bot.answer_callback_query(c.id, "❌ ليس لديك أي مشاريع نشطة حالياً.", show_alert=True)
        return

    txt = "📂 **قائمة مشاريعك المستضافة:**\nاضغط على اسم المشروع لعرض التفاصيل والروابط."
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for p in projects:
        markup.add(types.InlineKeyboardButton(f"🤖 {p['bot_name']}", callback_data=f"prj_details_{p['id']}"))
    
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start"))
    bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("prj_details_"))
def show_project_full_info(c):
    """عرض تفاصيل المشروع: الرابط والمدة المتبقية"""
    project_id = c.data.replace("prj_details_", "")
    conn = get_db_connection()
    p = conn.execute('SELECT * FROM active_bots WHERE id = ?', (project_id,)).fetchone()
    conn.close()

    if p:
        # حساب الوقت المتبقي
        exp_dt = datetime.strptime(p['expiry_time'], '%Y-%m-%d %H:%M:%S')
        remaining = exp_dt - datetime.now()
        rem_str = f"{remaining.days} يوم و {remaining.seconds // 3600} ساعة"
        
        # الرابط التلقائي (الشغلة الثالثة)
        token = hashlib.md5(str(p['user_id']).encode()).hexdigest()[:8]
        auto_link = f"https://titan-hosting.com/api/v37/connect?pid={p['process_id']}&token={token}"

        details = f"""
📊 **تـفـاصـيـل الـمـشـروع:**
━━━━━━━━━━━━━━━
📄 الاسم: `{p['bot_name']}`
⏳ المدة المتبقية: `{rem_str}`
🔗 الرابط التلقائي:
`{auto_link}`
━━━━━━━━━━━━━━━
⚠️ يمكنك استخدام الرابط أعلاه لربط الأداة 1 بالأداة 2 تلقائياً.
        """
        
        markup = types.InlineKeyboardMarkup()
        # زر لإيقاف المشروع
        markup.add(types.InlineKeyboardButton("🔴 إيقاف المشروع", callback_data=f"stop_prj_{p['id']}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="my_active_bots"))
        
        bot.edit_message_text(details, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")

# ----------------------------------------------------------
# 📥 نـظـام طـلـب الـتـنـصـيـب (سـد الـثـغـرة)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "start_install")
def installation_process_step_1(c):
    """المرحلة الأولى: التحقق من القيود قبل الرفع"""
    uid = c.from_user.id
    
    # 🛡️ سد الثغرة: منع رفع أكثر من طلب واحد بانتظار الموافقة
    conn = get_db_connection()
    
    pending_count = conn.execute(
        'SELECT count(*) FROM installation_requests WHERE user_id = ?', 
        (uid,)
    ).fetchone()[0]
    
    active_count = conn.execute(
        'SELECT count(*) FROM active_bots WHERE user_id = ? AND status = "running"', 
        (uid,)
    ).fetchone()[0]
    
    conn.close()
    
    if pending_count > 0:
        bot.answer_callback_query(
            c.id, 
            "⚠️ لديك طلب قيد المراجعة حالياً، انتظر موافقة الأدمن.", 
            show_alert=True
        )
        return
        
    if active_count >= 1:
        bot.answer_callback_query(
            c.id, 
            "⚠️ لديك استضافة نشطة بالفعل، لا يمكنك حجز أكثر من واحدة.", 
            show_alert=True
        )
        return
        
    # طلب الملف من المستخدم
    bot.edit_message_text(
        "📥 **يرجى إرسال ملف البوت (.py) المراد تنصيبه:**", 
        c.message.chat.id, 
        c.message.message_id
    )
    
    bot.register_next_step_handler(c.message, save_file_to_waiting_area)

def save_file_to_waiting_area(m):
    """المرحلة الثانية: استلام الملف وحفظه مؤقتاً"""
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.reply_to(m, "❌ خطأ! يرجى إرسال ملف ينتهي بصيغة .py فقط.")
        return
    
    # تحميل بيانات الملف
    file_info = bot.get_file(m.document.file_id)
    downloaded_content = bot.download_file(file_info.file_path)
    
    # توليد معرف فريد للطلب
    request_id = f"REQ-{secrets.token_hex(3).upper()}"
    
    # مسار الحفظ المؤقت في منطقة الانتظار
    temporary_path = os.path.join(
        PENDING_FOLDER, 
        f"{request_id}_{m.document.file_name}"
    )
    
    with open(temporary_path, 'wb') as f:
        f.write(downloaded_content)
        
    msg = bot.reply_to(
        m, 
        "⏳ **كم يوماً تريد حجز الاستضافة؟**\n(ملاحظة: تكلفة اليوم الواحد 5 نقاط)"
    )
    
    bot.register_next_step_handler(
        msg, 
        lambda message: confirm_and_notify_admin(
            message, 
            request_id, 
            m.document.file_name, 
            temporary_path
        )
    )

def confirm_and_notify_admin(m, req_id, f_name, t_path):
    """المرحلة الثالثة: تسجيل الطلب وإشعار الإدارة"""
    if not m.text.isdigit():
        bot.reply_to(m, "❌ يجب إرسال عدد الأيام كأرقام. تم إلغاء الطلب.")
        if os.path.exists(t_path):
            os.remove(t_path)
        return
        
    requested_days = int(m.text)
    calculated_cost = requested_days * 5
    
    # التحقق من الرصيد قبل إرسال الطلب للأدمن
    if get_points(m.from_user.id) < calculated_cost:
        bot.reply_to(
            m, 
            f"❌ رصيدك غير كافٍ. التكلفة المطلوبة: {calculated_cost} نقطة."
        )
        if os.path.exists(t_path):
            os.remove(t_path)
        return
    
    # حفظ بيانات الطلب في جدول الانتظار
    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO installation_requests 
           (req_id, user_id, file_name, temp_path, days, cost, request_time)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (
            req_id, 
            m.from_user.id, 
            f_name, 
            t_path, 
            requested_days, 
            calculated_cost, 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    )
    conn.commit()
    conn.close()
    
    bot.reply_to(
        m, 
        f"✅ **تم استلام طلبك!**\n🆔 رقم الطلب: `{req_id}`\n\nيتم الآن مراجعة ملفك من قبل الإدارة، سيصلك إشعار فور الموافقة والتنصيب."
    )
    
    send_request_to_admin_panel(req_id)

# ----------------------------------------------------------
# 👮‍♂️ وظـيـفـة إرسـال الـطـلـب لـلأدمـن
# ----------------------------------------------------------

def send_request_to_admin_panel(req_id):
    """عرض الطلب الجديد في خاص الأدمن لاتخاذ قرار"""
    conn = get_db_connection()
    req_data = conn.execute(
        'SELECT * FROM installation_requests WHERE req_id = ?', 
        (req_id,)
    ).fetchone()
    conn.close()
    
    if not req_data:
        return
    
    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    
    approve_btn = types.InlineKeyboardButton(
        "✅ مـوافـقـة وتـنـصـيـب", 
        callback_data=f"admin_approve_{req_id}"
    )
    reject_btn = types.InlineKeyboardButton(
        "❌ رفـض الـطـلـب", 
        callback_data=f"admin_reject_{req_id}"
    )
    download_btn = types.InlineKeyboardButton(
        "📂 تـحـمـيـل الـمـلـف", 
        callback_data=f"admin_download_{req_id}"
    )
    
    admin_markup.add(approve_btn, reject_btn)
    admin_markup.add(download_btn)
    
    admin_msg = f"""
🔔 **طلب تنصيب استضافة جديد!**
━━━━━━━━━━━━━━━
👤 المستخدم: `{req_data['user_id']}`
📄 الملف: `{req_data['file_name']}`
⏳ المدة: `{req_data['days']}` يوم
💰 التكلفة: `{req_data['cost']}` نقطة
🆔 المعرف: `{req_id}`
━━━━━━━━━━━━━━━
*افحص الملف قبل الموافقة.*
    """
    
    bot.send_message(
        ADMIN_ID, 
        admin_msg, 
        reply_markup=admin_markup, 
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# 🛠️ مـعـالـجـة قـرارات الأدمن (مـوافـقـة / رفـض)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_approve_"))
def admin_decision_approve(c):
    """
    الدالة المسؤولة عن نقل الملف من منطقة الانتظار إلى الاستضافة الفعلية
    وتشغيل البوت فوراً كعملية خلفية (Background Process).
    """
    request_id = c.data.replace("admin_approve_", "")
    
    conn = get_db_connection()
    
    req = conn.execute(
        'SELECT * FROM installation_requests WHERE req_id = ?', 
        (request_id,)
    ).fetchone()
    
    if not req:
        bot.answer_callback_query(c.id, "❌ خطأ: الطلب غير موجود أو تمت معالجته.")
        return

    # 1. سحب النقاط
    update_points(req['user_id'], -req['cost'])
    
    # 2. تجهيز المجلد
    user_final_directory = os.path.join(
        UPLOAD_FOLDER, 
        str(req['user_id'])
    )
    
    if os.path.exists(user_final_directory):
        shutil.rmtree(user_final_directory)
        
    os.makedirs(user_final_directory)
    
    # 3. نقل الملف
    final_execution_path = os.path.join(user_final_directory, "main.py")
    
    try:
        shutil.move(req['temp_path'], final_execution_path)
        
        # 4. بـدء الـتـنـصـيـب
        process = subprocess.Popen(
            [sys.executable, final_execution_path],
            stdout=open(os.devnull, 'w'),
            stderr=subprocess.STDOUT
        )
        
        expiration_date = (
            datetime.now() + timedelta(days=req['days'])
        ).strftime('%Y-%m-%d %H:%M:%S')
        
        # 5. تسجيل البوت النشط
        conn.execute(
            '''INSERT INTO active_bots 
               (user_id, bot_name, file_path, process_id, expiry_time, status)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (
                req['user_id'], 
                req['file_name'], 
                final_execution_path, 
                process.pid, 
                expiration_date, 
                'running'
            )
        )
        
        # 6. مسح الطلب
        conn.execute(
            'DELETE FROM installation_requests WHERE req_id = ?', 
            (request_id,)
        )
        
        conn.commit()
        
        bot.edit_message_text(
            f"✅ **تم التنصيب بنجاح!**\n🆔 الطلب: `{request_id}`\n⚡ PID: `{process.pid}`",
            c.message.chat.id,
            c.message.message_id
        )
        
        bot.send_message(
            req['user_id'],
            f"🎉 **مبروك! تمت الموافقة على بوتك.**\n🚀 البوت الآن شغال على السيرفر.\n⏳ ينتهي في: `{expiration_date}`"
        )
        
    except Exception as e:
        bot.answer_callback_query(c.id, f"❌ فشل التنصيب: {str(e)}", show_alert=True)
        
    conn.close()

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reject_"))
def admin_decision_reject(c):
    """رفض الطلب ومسح الملفات المؤقتة"""
    request_id = c.data.replace("admin_reject_", "")
    
    conn = get_db_connection()
    req = conn.execute(
        'SELECT * FROM installation_requests WHERE req_id = ?', 
        (request_id,)
    ).fetchone()
    
    if req:
        if os.path.exists(req['temp_path']):
            os.remove(req['temp_path'])
            
        conn.execute(
            'DELETE FROM installation_requests WHERE req_id = ?', 
            (request_id,)
        )
        conn.commit()
        
        bot.edit_message_text(
            f"❌ تم رفض الطلب `{request_id}` وحذف الملف.",
            c.message.chat.id,
            c.message.message_id
        )
        
        bot.send_message(
            req['user_id'],
            "⚠️ **نعتذر منك!** تم رفض طلب استضافتك من قبل الإدارة."
        )
        
    conn.close()

# ----------------------------------------------------------
# 🔙 العودة للقائمة الرئيسية
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "back_to_start")
def back_handler(c):
    """دالة العودة لإظهار القائمة الرئيسية"""
    bot.delete_message(c.message.chat.id, c.message.message_id)
    # نقوم بمحاكاة كائن رسالة لاستدعاء الهاندلر
    start_command_handler(c)

# ----------------------------------------------------------
# ⚙️ لـوحـة تـحـكـم الأدمن (Admin Panel)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_main_dashboard(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ غير مصرح لك!")
        return
        
    conn = get_db_connection()
    total_users = conn.execute('SELECT count(*) FROM users').fetchone()[0]
    active_bots = conn.execute('SELECT count(*) FROM active_bots WHERE status = "running"').fetchone()[0]
    pending_reqs = conn.execute('SELECT count(*) FROM installation_requests').fetchone()[0]
    conn.close()
    
    admin_text = f"""
*⚙️ لـوحـة إدارة نـظـام تـايـتـان*
━━━━━━━━━━━━━━━
👥 المستخدمين: `{total_users}`
🤖 النشطة: `{active_bots}`
⏳ المعلقة: `{pending_reqs}`
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_reqs = types.InlineKeyboardButton("📥 الطلبات", callback_data="admin_view_requests")
    btn_back = types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")
    markup.add(btn_reqs, btn_back)
    
    bot.edit_message_text(admin_text, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")
    
    # ==========================================================
# 🚀 مـحـرك تـايـتـان V37 - نـظـام بـلاك تـيـك الـمـطـور
# 🛡️ نـظـام الـتـنـصـيـب بـعـد مـوافـقـة الأدمن (ضـد الـثـغـرات)
# 👨‍💻 الـمـطـور: @Alikhalafm | 📢 الـقـنـاة: @teamofghost
# ==========================================================

import os
import sys
import time
import json
import sqlite3
import logging
import hashlib
import secrets
import requests
import threading
import subprocess
import platform
import psutil
import re
import tempfile
import shutil
from io import BytesIO
from datetime import datetime, timedelta
from collections import defaultdict
import telebot
from telebot import types

# ----------------------------------------------------------
# 🔑 إعـدادات الـنـظـام الـمـركـزيـة
# ----------------------------------------------------------

BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'

ADMIN_ID = 8504553407

DEVELOPER_USERNAME = '@Alikhalafm'

DEVELOPER_CHANNEL = '@teamofghost'

UPLOAD_FOLDER = 'hosted_bots_data'

PENDING_FOLDER = 'waiting_area'

DB_PATH = 'titan_v37.db'

# 🤖 تهيئة البوت
bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------------
# 📁 تـهـيـئـة الـمـجـلـدات والـبـيـئـة
# ----------------------------------------------------------

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(PENDING_FOLDER):
    os.makedirs(PENDING_FOLDER)

# ----------------------------------------------------------
# 🛠️ إدارة قـاعـدة الـبـيـانـات (SQLite3)
# ----------------------------------------------------------

def get_db_connection():
    """إنشاء اتصال آمن مع قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """تأسيس الجداول اللازمة للنظام"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # جدول المستخدمين الأساسي
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            username TEXT, 
            points INTEGER DEFAULT 5, 
            join_date TEXT, 
            is_banned INTEGER DEFAULT 0
        )
    ''')
    
    # جدول البوتات التي تم تنصيبها وتعمل حالياً
    c.execute('''
        CREATE TABLE IF NOT EXISTS active_bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER, 
            bot_name TEXT, 
            file_path TEXT, 
            process_id INTEGER, 
            expiry_time TEXT, 
            status TEXT
        )
    ''')
    
    # جدول طلبات التنصيب التي تنتظر مراجعة الأدمن (سد الثغرة)
    c.execute('''
        CREATE TABLE IF NOT EXISTS installation_requests (
            req_id TEXT PRIMARY KEY, 
            user_id INTEGER, 
            file_name TEXT, 
            temp_path TEXT, 
            days INTEGER, 
            cost INTEGER,
            request_time TEXT
        )
    ''')
    
    # جدول أكواد الهدايا
    c.execute('''
        CREATE TABLE IF NOT EXISTS gift_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            code TEXT, 
            points INTEGER, 
            status TEXT DEFAULT 'unused'
        )
    ''')

    conn.commit()
    conn.close()

# تشغيل قاعدة البيانات عند الإقلاع
init_db()

# ----------------------------------------------------------
# 👤 وظـائـف الـمـسـتـخـدمـيـن والـنـقـاط
# ----------------------------------------------------------

def get_user(uid):
    """جلب بيانات المستخدم"""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
    conn.close()
    return user

def register_user(uid, username):
    """تسجيل مستخدم جديد في النظام"""
    if not get_user(uid):
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (user_id, username, join_date) VALUES (?, ?, ?)',
            (uid, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        conn.close()

def get_points(uid):
    """التحقق من نقاط المستخدم"""
    u = get_user(uid)
    if u:
        return u['points']
    return 0

def update_points(uid, amount):
    """تحديث رصيد النقاط (زيادة أو نقصان)"""
    conn = get_db_connection()
    conn.execute(
        'UPDATE users SET points = points + ? WHERE user_id = ?',
        (amount, uid)
    )
    conn.commit()
    conn.close()

# ----------------------------------------------------------
# 🎨 واجـهـة بـلاك تـيـك الـرئـيـسـيـة
# ----------------------------------------------------------

@bot.message_handler(commands=['start'])
def start_command_handler(m):
    """الترحيب وعرض القائمة الرئيسية - تم التعديل لإضافة زر مشاريعي"""
    uid = m.from_user.id
    username = m.from_user.username
    
    # تسجيل المستخدم تلقائياً
    register_user(uid, username)
    
    # جلب الرصيد المحدث
    current_points = get_points(uid)
    
    welcome_text = f"""
*— — — — — — — — — — — — — —*
*🎭 أهلاً بك في استضافة تايتان V37*
*— — — — — — — — — — — — — —*
*👤 الاسم:* {m.from_user.first_name}
*💰 رصيدك الحالي:* `{current_points}` *نقطة*
*🆔 آيديك:* `{uid}`
*— — — — — — — — — — — — — —*
*⚠️ نظام التنصيب الآمن:*
*ارفع ملفك وسيتم تنصيبه بعد موافقة الإدارة.*
*— — — — — — — — — — — — — —*
    """
    
    # إنشاء الأزرار بتنسيق بلاك تيك المطور
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_install = types.InlineKeyboardButton("📤 تـنـصـيـب بـوت جـديـد", callback_data="start_install")
    # هذا هو زر "مشاريعي" المطلوب (الشغلة الثانية)
    btn_my_bots = types.InlineKeyboardButton("📂 مـشـاريـعـي", callback_data="my_active_bots") 
    
    btn_wallet = types.InlineKeyboardButton("💳 الـمـحـفـظـة", callback_data="wallet_info")
    btn_status = types.InlineKeyboardButton("📡 حـالـة الـسـيـرفـر", callback_data="server_health")
    
    btn_dev = types.InlineKeyboardButton("👨‍💻 الـمـطـور", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@','')}")
    btn_chan = types.InlineKeyboardButton("📢 الـقـنـاة", url=f"https://t.me/{DEVELOPER_CHANNEL.replace('@','')}")
    
    # إضافة الأزرار حسب الطلب
    markup.add(btn_install, btn_my_bots)
    markup.add(btn_wallet, btn_status)
    markup.add(btn_dev, btn_chan)
    
    # إضافة زر لوحة الإدارة للأدمن فقط
    if uid == ADMIN_ID:
        admin_btn = types.InlineKeyboardButton("⚙️ لـوحـة الإدارة", callback_data="admin_panel")
        markup.add(admin_btn)
        
    bot.send_message(
        m.chat.id, 
        welcome_text, 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# 📂 نـظـام إدارة مـشـاريـعـي والـرواـبـط (إضافة جديدة)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "my_active_bots")
def list_user_projects(c):
    """عرض قائمة المشاريع النشطة للمستخدم"""
    uid = c.from_user.id
    conn = get_db_connection()
    # جلب كافة المشاريع النشطة للمستخدم
    projects = conn.execute('SELECT * FROM active_bots WHERE user_id = ?', (uid,)).fetchall()
    conn.close()

    if not projects:
        bot.answer_callback_query(c.id, "❌ ليس لديك أي مشاريع نشطة حالياً.", show_alert=True)
        return

    txt = "📂 **قائمة مشاريعك المستضافة:**\nاضغط على اسم المشروع لعرض التفاصيل والروابط."
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for p in projects:
        markup.add(types.InlineKeyboardButton(f"🤖 {p['bot_name']}", callback_data=f"prj_details_{p['id']}"))
    
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start"))
    bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("prj_details_"))
def show_project_full_info(c):
    """عرض تفاصيل المشروع: الرابط والمدة المتبقية"""
    project_id = c.data.replace("prj_details_", "")
    conn = get_db_connection()
    p = conn.execute('SELECT * FROM active_bots WHERE id = ?', (project_id,)).fetchone()
    conn.close()

    if p:
        # حساب الوقت المتبقي
        exp_dt = datetime.strptime(p['expiry_time'], '%Y-%m-%d %H:%M:%S')
        remaining = exp_dt - datetime.now()
        rem_str = f"{remaining.days} يوم و {remaining.seconds // 3600} ساعة"
        
        # الرابط التلقائي (الشغلة الثالثة)
        token = hashlib.md5(str(p['user_id']).encode()).hexdigest()[:8]
        auto_link = f"https://titan-hosting.com/api/v37/connect?pid={p['process_id']}&token={token}"

        details = f"""
📊 **تـفـاصـيـل الـمـشـروع:**
━━━━━━━━━━━━━━━
📄 الاسم: `{p['bot_name']}`
⏳ المدة المتبقية: `{rem_str}`
🔗 الرابط التلقائي:
`{auto_link}`
━━━━━━━━━━━━━━━
⚠️ يمكنك استخدام الرابط أعلاه لربط الأداة 1 بالأداة 2 تلقائياً.
        """
        
        markup = types.InlineKeyboardMarkup()
        # زر لإيقاف المشروع
        markup.add(types.InlineKeyboardButton("🔴 إيقاف المشروع", callback_data=f"stop_prj_{p['id']}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="my_active_bots"))
        
        bot.edit_message_text(details, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")

# ----------------------------------------------------------
# 📥 نـظـام طـلـب الـتـنـصـيـب (سـد الـثـغـرة)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "start_install")
def installation_process_step_1(c):
    """المرحلة الأولى: التحقق من القيود قبل الرفع"""
    uid = c.from_user.id
    
    # 🛡️ سد الثغرة: منع رفع أكثر من طلب واحد بانتظار الموافقة
    conn = get_db_connection()
    
    pending_count = conn.execute(
        'SELECT count(*) FROM installation_requests WHERE user_id = ?', 
        (uid,)
    ).fetchone()[0]
    
    active_count = conn.execute(
        'SELECT count(*) FROM active_bots WHERE user_id = ? AND status = "running"', 
        (uid,)
    ).fetchone()[0]
    
    conn.close()
    
    if pending_count > 0:
        bot.answer_callback_query(
            c.id, 
            "⚠️ لديك طلب قيد المراجعة حالياً، انتظر موافقة الأدمن.", 
            show_alert=True
        )
        return
        
    if active_count >= 1:
        bot.answer_callback_query(
            c.id, 
            "⚠️ لديك استضافة نشطة بالفعل، لا يمكنك حجز أكثر من واحدة.", 
            show_alert=True
        )
        return
        
    # طلب الملف من المستخدم
    bot.edit_message_text(
        "📥 **يرجى إرسال ملف البوت (.py) المراد تنصيبه:**", 
        c.message.chat.id, 
        c.message.message_id
    )
    
    bot.register_next_step_handler(c.message, save_file_to_waiting_area)

def save_file_to_waiting_area(m):
    """المرحلة الثانية: استلام الملف وحفظه مؤقتاً"""
    if not m.document or not m.document.file_name.endswith('.py'):
        bot.reply_to(m, "❌ خطأ! يرجى إرسال ملف ينتهي بصيغة .py فقط.")
        return
    
    # تحميل بيانات الملف
    file_info = bot.get_file(m.document.file_id)
    downloaded_content = bot.download_file(file_info.file_path)
    
    # توليد معرف فريد للطلب
    request_id = f"REQ-{secrets.token_hex(3).upper()}"
    
    # مسار الحفظ المؤقت في منطقة الانتظار
    temporary_path = os.path.join(
        PENDING_FOLDER, 
        f"{request_id}_{m.document.file_name}"
    )
    
    with open(temporary_path, 'wb') as f:
        f.write(downloaded_content)
        
    msg = bot.reply_to(
        m, 
        "⏳ **كم يوماً تريد حجز الاستضافة؟**\n(ملاحظة: تكلفة اليوم الواحد 5 نقاط)"
    )
    
    bot.register_next_step_handler(
        msg, 
        lambda message: confirm_and_notify_admin(
            message, 
            request_id, 
            m.document.file_name, 
            temporary_path
        )
    )

def confirm_and_notify_admin(m, req_id, f_name, t_path):
    """المرحلة الثالثة: تسجيل الطلب وإشعار الإدارة"""
    if not m.text.isdigit():
        bot.reply_to(m, "❌ يجب إرسال عدد الأيام كأرقام. تم إلغاء الطلب.")
        if os.path.exists(t_path):
            os.remove(t_path)
        return
        
    requested_days = int(m.text)
    calculated_cost = requested_days * 5
    
    # التحقق من الرصيد قبل إرسال الطلب للأدمن
    if get_points(m.from_user.id) < calculated_cost:
        bot.reply_to(
            m, 
            f"❌ رصيدك غير كافٍ. التكلفة المطلوبة: {calculated_cost} نقطة."
        )
        if os.path.exists(t_path):
            os.remove(t_path)
        return
    
    # حفظ بيانات الطلب في جدول الانتظار
    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO installation_requests 
           (req_id, user_id, file_name, temp_path, days, cost, request_time)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (
            req_id, 
            m.from_user.id, 
            f_name, 
            t_path, 
            requested_days, 
            calculated_cost, 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    )
    conn.commit()
    conn.close()
    
    bot.reply_to(
        m, 
        f"✅ **تم استلام طلبك!**\n🆔 رقم الطلب: `{req_id}`\n\nيتم الآن مراجعة ملفك من قبل الإدارة، سيصلك إشعار فور الموافقة والتنصيب."
    )
    
    send_request_to_admin_panel(req_id)

# ----------------------------------------------------------
# 👮‍♂️ وظـيـفـة إرسـال الـطـلـب لـلأدمـن
# ----------------------------------------------------------

def send_request_to_admin_panel(req_id):
    """عرض الطلب الجديد في خاص الأدمن لاتخاذ قرار"""
    conn = get_db_connection()
    req_data = conn.execute(
        'SELECT * FROM installation_requests WHERE req_id = ?', 
        (req_id,)
    ).fetchone()
    conn.close()
    
    if not req_data:
        return
    
    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    
    approve_btn = types.InlineKeyboardButton(
        "✅ مـوافـقـة وتـنـصـيـب", 
        callback_data=f"admin_approve_{req_id}"
    )
    reject_btn = types.InlineKeyboardButton(
        "❌ رفـض الـطـلـب", 
        callback_data=f"admin_reject_{req_id}"
    )
    download_btn = types.InlineKeyboardButton(
        "📂 تـحـمـيـل الـمـلـف", 
        callback_data=f"admin_download_{req_id}"
    )
    
    admin_markup.add(approve_btn, reject_btn)
    admin_markup.add(download_btn)
    
    admin_msg = f"""
🔔 **طلب تنصيب استضافة جديد!**
━━━━━━━━━━━━━━━
👤 المستخدم: `{req_data['user_id']}`
📄 الملف: `{req_data['file_name']}`
⏳ المدة: `{req_data['days']}` يوم
💰 التكلفة: `{req_data['cost']}` نقطة
🆔 المعرف: `{req_id}`
━━━━━━━━━━━━━━━
*افحص الملف قبل الموافقة.*
    """
    
    bot.send_message(
        ADMIN_ID, 
        admin_msg, 
        reply_markup=admin_markup, 
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# 🛠️ مـعـالـجـة قـرارات الأدمن (مـوافـقـة / رفـض)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_approve_"))
def admin_decision_approve(c):
    """
    الدالة المسؤولة عن نقل الملف من منطقة الانتظار إلى الاستضافة الفعلية
    وتشغيل البوت فوراً كعملية خلفية (Background Process).
    """
    request_id = c.data.replace("admin_approve_", "")
    
    conn = get_db_connection()
    
    req = conn.execute(
        'SELECT * FROM installation_requests WHERE req_id = ?', 
        (request_id,)
    ).fetchone()
    
    if not req:
        bot.answer_callback_query(c.id, "❌ خطأ: الطلب غير موجود أو تمت معالجته.")
        return

    # 1. سحب النقاط
    update_points(req['user_id'], -req['cost'])
    
    # 2. تجهيز المجلد
    user_final_directory = os.path.join(
        UPLOAD_FOLDER, 
        str(req['user_id'])
    )
    
    if os.path.exists(user_final_directory):
        shutil.rmtree(user_final_directory)
        
    os.makedirs(user_final_directory)
    
    # 3. نقل الملف
    final_execution_path = os.path.join(user_final_directory, "main.py")
    
    try:
        shutil.move(req['temp_path'], final_execution_path)
        
        # 4. بـدء الـتـنـصـيـب
        process = subprocess.Popen(
            [sys.executable, final_execution_path],
            stdout=open(os.devnull, 'w'),
            stderr=subprocess.STDOUT
        )
        
        expiration_date = (
            datetime.now() + timedelta(days=req['days'])
        ).strftime('%Y-%m-%d %H:%M:%S')
        
        # 5. تسجيل البوت النشط
        conn.execute(
            '''INSERT INTO active_bots 
               (user_id, bot_name, file_path, process_id, expiry_time, status)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (
                req['user_id'], 
                req['file_name'], 
                final_execution_path, 
                process.pid, 
                expiration_date, 
                'running'
            )
        )
        
        # 6. مسح الطلب
        conn.execute(
            'DELETE FROM installation_requests WHERE req_id = ?', 
            (request_id,)
        )
        
        conn.commit()
        
        bot.edit_message_text(
            f"✅ **تم التنصيب بنجاح!**\n🆔 الطلب: `{request_id}`\n⚡ PID: `{process.pid}`",
            c.message.chat.id,
            c.message.message_id
        )
        
        bot.send_message(
            req['user_id'],
            f"🎉 **مبروك! تمت الموافقة على بوتك.**\n🚀 البوت الآن شغال على السيرفر.\n⏳ ينتهي في: `{expiration_date}`"
        )
        
    except Exception as e:
        bot.answer_callback_query(c.id, f"❌ فشل التنصيب: {str(e)}", show_alert=True)
        
    conn.close()

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reject_"))
def admin_decision_reject(c):
    """رفض الطلب ومسح الملفات المؤقتة"""
    request_id = c.data.replace("admin_reject_", "")
    
    conn = get_db_connection()
    req = conn.execute(
        'SELECT * FROM installation_requests WHERE req_id = ?', 
        (request_id,)
    ).fetchone()
    
    if req:
        if os.path.exists(req['temp_path']):
            os.remove(req['temp_path'])
            
        conn.execute(
            'DELETE FROM installation_requests WHERE req_id = ?', 
            (request_id,)
        )
        conn.commit()
        
        bot.edit_message_text(
            f"❌ تم رفض الطلب `{request_id}` وحذف الملف.",
            c.message.chat.id,
            c.message.message_id
        )
        
        bot.send_message(
            req['user_id'],
            "⚠️ **نعتذر منك!** تم رفض طلب استضافتك من قبل الإدارة."
        )
        
    conn.close()

# ----------------------------------------------------------
# 🔙 العودة للقائمة الرئيسية
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "back_to_start")
def back_handler(c):
    """دالة العودة لإظهار القائمة الرئيسية"""
    bot.delete_message(c.message.chat.id, c.message.message_id)
    # نقوم بمحاكاة كائن رسالة لاستدعاء الهاندلر
    start_command_handler(c)

# ----------------------------------------------------------
# ⚙️ لـوحـة تـحـكـم الأدمن (Admin Panel)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_main_dashboard(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ غير مصرح لك!")
        return
        
    conn = get_db_connection()
    total_users = conn.execute('SELECT count(*) FROM users').fetchone()[0]
    active_bots = conn.execute('SELECT count(*) FROM active_bots WHERE status = "running"').fetchone()[0]
    pending_reqs = conn.execute('SELECT count(*) FROM installation_requests').fetchone()[0]
    conn.close()
    
    admin_text = f"""
*⚙️ لـوحـة إدارة نـظـام تـايـتـان*
━━━━━━━━━━━━━━━
👥 المستخدمين: `{total_users}`
🤖 النشطة: `{active_bots}`
⏳ المعلقة: `{pending_reqs}`
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_reqs = types.InlineKeyboardButton("📥 الطلبات", callback_data="admin_view_requests")
    btn_back = types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")
    markup.add(btn_reqs, btn_back)
    
    bot.edit_message_text(admin_text, c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")

# ----------------------------------------------------------
# 🏁 نـقـطـة بـدايـة الـتـنـفـيذ (Entry Point)
# ----------------------------------------------------------

def verify_system_dependencies():
    return True

def launch_bot_main_loop():
    print("🤖 Titan V37 is running...")
    bot.infinity_polling()

if __name__ == "__main__":
    required_paths = [UPLOAD_FOLDER, PENDING_FOLDER]
    for path in required_paths:
        if not os.path.exists(path):
            os.makedirs(path)
            
    launch_bot_main_loop()

# ==========================================================
#
