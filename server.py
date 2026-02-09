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
    """الترحيب وعرض القائمة الرئيسية"""
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
    
    # إنشاء الأزرار بتنسيق بلاك تيك
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_install = types.InlineKeyboardButton("📤 تـنـصـيـب بـوت جـديـد", callback_data="start_install")
    btn_my_bots = types.InlineKeyboardButton("🤖 بـوتـاتـي الـنـشـطـة", callback_data="my_active_bots")
    
    btn_wallet = types.InlineKeyboardButton("💳 الـمـحـفـظـة", callback_data="wallet_info")
    btn_status = types.InlineKeyboardButton("📡 حـالـة الـسـيـرفـر", callback_data="server_health")
    
    btn_dev = types.InlineKeyboardButton("👨‍💻 الـمـطـور", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@','')}")
    btn_chan = types.InlineKeyboardButton("📢 الـقـنـاة", url=f"https://t.me/{DEVELOPER_CHANNEL.replace('@','')}")
    
    markup.add(btn_install, btn_my_bots)
    markup.add(btn_wallet, btn_status)
    markup.add(btn_dev, btn_chan)
    
    # إضافة زر لوحة الإدارة للأدمن فقط
    if uid == ADMIN_ID:
        admin_btn = types.InlineKeyboardButton("⚙️ لـوحـة الإدارة", callback_data="admin_panel")
        markup.add(admin_btn)
        
    # زر مشاريعي كزر لوحة (بدون كتابة نص)
    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add(types.KeyboardButton("📁 مشاريعي"))
    bot.send_message(
        m.chat.id, 
        welcome_text, 
        reply_markup=reply_kb, 
        parse_mode="Markdown"
    )
    # إرسال الأزرار الإنلاين برسالة ثانية
    bot.send_message(
        m.chat.id,
        "اختر من القائمة:",
        reply_markup=markup
    )

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
    
    # وظيفة إرسال الإشعار للأدمن (سيتم تعريفها في الجزء التالي)
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

# نهاية الجزء الأول (الأسطر 1-300 فعلياً في Visual Studio)
# ..........................................................
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
    
    # جلب بيانات الطلب من قاعدة البيانات
    req = conn.execute(
        'SELECT * FROM installation_requests WHERE req_id = ?', 
        (request_id,)
    ).fetchone()
    
    if not req:
        bot.answer_callback_query(c.id, "❌ خطأ: الطلب غير موجود أو تمت معالجته.")
        return

    # 1. سحب النقاط من رصيد المستخدم (التنفيذ المالي)
    update_points(req['user_id'], -req['cost'])
    
    # 2. تجهيز المجلد الرسمي للاستضافة (عزل المستخدم)
    user_final_directory = os.path.join(
        UPLOAD_FOLDER, 
        str(req['user_id'])
    )
    
    # تنظيف أي ملفات قديمة لضمان عدم تداخل الملفات (سد ثغرة التعدد)
    if os.path.exists(user_final_directory):
        shutil.rmtree(user_final_directory)
        
    os.makedirs(user_final_directory)
    
    # 3. نقل الملف وتغيير اسمه إلى اسم موحد للتشغيل
    final_execution_path = os.path.join(user_final_directory, "main.py")
    
    try:
        shutil.move(req['temp_path'], final_execution_path)
        
        # 4. بـدء الـتـنـصـيـب والـتـشـغـيـل (Deployment)
        # تشغيل الملف باستخدام نسخة بايثون الحالية في السيرفر
        process = subprocess.Popen(
            [sys.executable, final_execution_path],
            stdout=open(os.devnull, 'w'),
            stderr=subprocess.STDOUT
        )
        
        # حساب تاريخ انتهاء الاستضافة
        expiration_date = (
            datetime.now() + timedelta(days=req['days'])
        ).strftime('%Y-%m-%d %H:%M:%S')
        
        # 5. تسجيل البوت في قائمة الاستضافات النشطة
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
        
        # 6. مسح الطلب من قائمة الانتظار
        conn.execute(
            'DELETE FROM installation_requests WHERE req_id = ?', 
            (request_id,)
        )
        
        conn.commit()
        
        # إشعار الأدمن بالنجاح
        bot.edit_message_text(
            f"✅ **تم التنصيب بنجاح!**\n🆔 الطلب: `{request_id}`\n⚡ PID: `{process.pid}`",
            c.message.chat.id,
            c.message.message_id
        )
        
        # إشعار الزبون بالتشغيل
        bot.send_message(
            req['user_id'],
            f"🎉 **مبروك! تمت الموافقة على بوتك.**\n🚀 البوت الآن شغال على السيرفر.\n⏳ ينتهي في: `{expiration_date}`"
        )
        
    except Exception as e:
        bot.answer_callback_query(c.id, f"❌ فشل التنصيب: {str(e)}", show_alert=True)
        
    conn.close()

# ----------------------------------------------------------
# ❌ نـظـام رفـض الـطـلـب (Rejection System)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reject_"))
def admin_decision_reject(c):
    """رفض الطلب ومسح الملفات المؤقتة لمنع تراكم الملفات الخبيثة"""
    request_id = c.data.replace("admin_reject_", "")
    
    conn = get_db_connection()
    req = conn.execute(
        'SELECT * FROM installation_requests WHERE req_id = ?', 
        (request_id,)
    ).fetchone()
    
    if req:
        # حذف الملف المؤقت فوراً
        if os.path.exists(req['temp_path']):
            os.remove(req['temp_path'])
            
        # حذف السجل من قاعدة البيانات
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
        
        # إبلاغ المستخدم بالرفض
        bot.send_message(
            req['user_id'],
            "⚠️ **نعتذر منك!** تم رفض طلب استضافتك من قبل الإدارة.\nتأكد من سلامة الكود وحاول مجدداً."
        )
        
    conn.close()

# ----------------------------------------------------------
# 📂 تـحـمـيـل الـمـلـف لـلأدمـن (Security Inspection)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_download_"))
def admin_download_to_check(c):
    """إرسال الملف للأدمن في المحادثة لغرض الفحص اليدوي"""
    request_id = c.data.replace("admin_download_", "")
    
    conn = get_db_connection()
    req = conn.execute(
        'SELECT * FROM installation_requests WHERE req_id = ?', 
        (request_id,)
    ).fetchone()
    conn.close()
    
    if req and os.path.exists(req['temp_path']):
        with open(req['temp_path'], 'rb') as f:
            bot.send_document(
                c.message.chat.id, 
                f, 
                caption=f"📄 ملف المستخدم: `{req['user_id']}`\n🆔 الطلب: `{request_id}`"
            )
        bot.answer_callback_query(c.id, "✅ تم إرسال الملف.")
    else:
        bot.answer_callback_query(c.id, "❌ الملف غير موجود!")

# ----------------------------------------------------------
# 🏦 إدارة الـمـحـفـظـة (Wallet UI)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "wallet_info")
def display_wallet(c):
    """عرض تفاصيل رصيد المستخدم وخيارات الشحن"""
    uid = c.from_user.id
    user_data = get_user(uid)
    
    wallet_text = f"""
*— — — — — — — — — — — — — —*
*🏦 مـحـفـظـة تـايـتـان الـرقمـيـة*
*— — — — — — — — — — — — — —*
*💰 رصيدك الحالي:* `{user_data['points']}` *نقطة*
*🆔 آيديك:* `{uid}`
*— — — — — — — — — — — — — —*
*لشحن رصيدك، استخدم كود الهدية أو تواصل مع المطور.*
*— — — — — — — — — — — — — —*
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_redeem = types.InlineKeyboardButton("🎟 تفعيل كود", callback_data="redeem_gift")
    btn_buy = types.InlineKeyboardButton("➕ شراء نقاط", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@','')}")
    btn_back = types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")
    
    markup.add(btn_redeem, btn_buy)
    markup.add(btn_back)
    
    bot.edit_message_text(
        wallet_text,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# 🔙 العودة للقائمة الرئيسية
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "back_to_start")
def back_handler(c):
    """دالة العودة لمسح الرسالة الحالية وإظهار القائمة الرئيسية"""
    bot.delete_message(c.message.chat.id, c.message.message_id)
    # استدعاء دالة البداية (ستحتاج لتمرير كائن يحاكي الرسالة)
    start_command_handler(c)

# نهاية الجزء الثاني (الأسطر 301-600 فعلياً في Visual Studio)
# ..........................................................
# ----------------------------------------------------------
# ⚙️ لـوحـة تـحـكـم الأدمن الـشـامـلـة (Admin Panel)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_main_dashboard(c):
    """
    الواجهة المركزية للأدمن لإدارة كافة جوانب السيرفر والاستضافات.
    تتضمن إحصائيات سريعة وأزرار الوصول للأقسام المختلفة.
    """
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ غير مصرح لك بالدخول!")
        return
        
    conn = get_db_connection()
    
    # جلب إحصائيات سريعة للوحة التحكم
    total_users = conn.execute('SELECT count(*) FROM users').fetchone()[0]
    active_bots = conn.execute('SELECT count(*) FROM active_bots WHERE status = "running"').fetchone()[0]
    pending_reqs = conn.execute('SELECT count(*) FROM installation_requests').fetchone()[0]
    
    conn.close()
    
    admin_text = f"""
*— — — — — — — — — — — — — —*
*⚙️ لـوحـة إدارة نـظـام تـايـتـان*
*— — — — — — — — — — — — — —*
*👥 إجمالي المستخدمين:* `{total_users}`
*🤖 الاستضافات النشطة:* `{active_bots}`
*⏳ طلبات بانتظار الموافقة:* `{pending_reqs}`
*— — — — — — — — — — — — — —*
*اختر القسم المراد إدارته من الأسفل:*
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_reqs = types.InlineKeyboardButton("📥 إدارة الـطـلـبـات", callback_data="admin_view_requests")
    btn_codes = types.InlineKeyboardButton("🎁 تـولـيـد أكـواد", callback_data="admin_gen_codes")
    
    btn_users = types.InlineKeyboardButton("👤 إدارة الـمـسـتـخـدمـيـن", callback_data="admin_manage_users")
    btn_stats = types.InlineKeyboardButton("📊 إحـصـائـيـات الـسـيـرفـر", callback_data="server_health")
    
    btn_bc = types.InlineKeyboardButton("📢 إذاعـة عـامـة", callback_data="admin_broadcast")
    btn_back = types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_start")
    
    markup.add(btn_reqs, btn_codes)
    markup.add(btn_users, btn_stats)
    markup.add(btn_bc, btn_back)
    
    bot.edit_message_text(
        admin_text,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# 📥 قـائـمـة الـطـلـبـات الـمـعـلـقـة (Pending Requests List)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "admin_view_requests")
def list_pending_installation_requests(c):
    """عرض قائمة بجميع الطلبات التي تنتظر موافقة الأدمن"""
    conn = get_db_connection()
    
    requests_list = conn.execute(
        'SELECT * FROM installation_requests ORDER BY request_time DESC'
    ).fetchall()
    
    conn.close()
    
    if not requests_list:
        bot.answer_callback_query(c.id, "📭 لا توجد طلبات معلقة حالياً.", show_alert=True)
        return
        
    txt = "📂 **قائمة طلبات التنصيب المعلقة:**\n"
    txt += "━━━━━━━━━━━━━━━\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for req in requests_list:
        # عرض الآيدي واسم الملف في الزر
        button_label = f"🆔 {req['req_id']} | 📄 {req['file_name'][:15]}"
        markup.add(
            types.InlineKeyboardButton(
                button_label, 
                callback_data=f"view_req_details_{req['req_id']}"
            )
        )
        
    markup.add(types.InlineKeyboardButton("🔙 العودة للوحة الإدارة", callback_data="admin_panel"))
    
    bot.edit_message_text(
        txt,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# 🔍 عـرض تـفـاصـيـل طـلـب مـحـدد
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("view_req_details_"))
def show_request_full_info(c):
    """عرض بيانات الطلب بالكامل لاتخاذ قرار النهائي"""
    request_id = c.data.replace("view_req_details_", "")
    
    conn = get_db_connection()
    req = conn.execute(
        'SELECT * FROM installation_requests WHERE req_id = ?', 
        (request_id,)
    ).fetchone()
    conn.close()
    
    if not req:
        bot.answer_callback_query(c.id, "❌ هذا الطلب لم يعد متاحاً.")
        admin_main_dashboard(c)
        return
        
    details = f"""
📄 **تـفـاصـيـل طـلـب الـتـنـصـيـب:**
━━━━━━━━━━━━━━━
🆔 الـمـعـرف: `{req['req_id']}`
👤 الـمـسـتـخـدم: `{req['user_id']}`
📄 اسـم الـمـلـف: `{req['file_name']}`
⏳ مـدة الـحـجـز: `{req['days']}` يوم
💰 الـتـكـلـفـة: `{req['cost']}` نقطة
⏰ الـتـوقـيـت: `{req['request_time']}`
━━━━━━━━━━━━━━━
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_approve = types.InlineKeyboardButton("✅ موافقة", callback_data=f"admin_approve_{request_id}")
    btn_reject = types.InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_{request_id}")
    btn_dl = types.InlineKeyboardButton("📂 تحميل الملف", callback_data=f"admin_download_{request_id}")
    btn_back = types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_view_requests")
    
    markup.add(btn_approve, btn_reject)
    markup.add(btn_dl, btn_back)
    
    bot.edit_message_text(
        details,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# 🎁 نـظـام تـولـيـد الأكـواد (Gift Code Generator)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "admin_gen_codes")
def start_code_generation(c):
    """بدء عملية إنشاء كود هدية جديد"""
    bot.edit_message_text(
        "🔢 **أرسل كمية النقاط التي تريد وضعها في الكود:**",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 إلغاء", callback_data="admin_panel")
        )
    )
    bot.register_next_step_handler(c.message, execute_code_creation)

def execute_code_creation(m):
    """توليد الكود وحفظه في قاعدة البيانات"""
    if not m.text.isdigit():
        bot.reply_to(m, "❌ يرجى إرسال رقم صحيح فقط.")
        return
        
    points_value = int(m.text)
    
    # توليد كود عشوائي فريد
    generated_code = f"BLACK-{secrets.token_hex(4).upper()}"
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO gift_codes (code, points, status) VALUES (?, ?, ?)',
        (generated_code, points_value, 'unused')
    )
    conn.commit()
    conn.close()
    
    result_text = f"""
✅ **تم إنشاء كود الهدية بنجاح!**
━━━━━━━━━━━━━━━
🎫 الـكـود: `{generated_code}`
💰 الـقـيـمـة: `{points_value}` نقطة
━━━━━━━━━━━━━━━
*يمكنك الآن نسخ الكود وإرساله للمستخدم.*
    """
    bot.reply_to(m, result_text, parse_mode="Markdown")

# ----------------------------------------------------------
# 📡 مـراقـبـة مـوارد الـسـيـرفـر (System Monitoring)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "server_health")
def show_server_system_stats(c):
    """عرض حالة المعالج والرام والقرص الصلب للسيرفر"""
    
    # استخدام مكتبة psutil لجلب البيانات الحقيقية
    cpu_percent = psutil.cpu_percent(interval=0.5)
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    system_txt = f"""
*— — — — — — — — — — — — — —*
*📡 مـراقـبـة أداء الـنـظـام*
*— — — — — — — — — — — — — —*
*⚙️ الـمـعـالـج (CPU):* `{cpu_percent}%`
*📟 الـرام (RAM):* `{ram_usage}%`
*💾 الـقـرص (Disk):* `{disk_usage}%`
*— — — — — — — — — — — — — —*
*الحالة العامة:* `مستقر ✅`
*— — — — — — — — — — — — — —*
    """
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="server_health"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    
    bot.edit_message_text(
        system_txt,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# نهاية الجزء الثالث (الأسطر 601-900 فعلياً في Visual Studio)
# ..........................................................
# ----------------------------------------------------------
# 👤 نـظـام إدارة الـمـسـتـخـدمـيـن (User Management)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "admin_manage_users")
def admin_user_search_prompt(c):
    """
    هذه الدالة تطلب من الأدمن إرسال آيدي المستخدم المراد إدارته.
    تستخدم للبحث السريع وتعديل صلاحيات المستخدمين.
    """
    if c.from_user.id != ADMIN_ID:
        return

    instruction_text = """
🔍 **إدارة الـمـسـتـخـدمـيـن:**
━━━━━━━━━━━━━━━
يرجى إرسال **آيـدي (ID)** المستخدم الذي تريد:
• حـظـره مـن الـنـظـام.
• إضافة أو خـصـم نـقـاط.
• مـعـايـنـة بـوتـاتـه الـنـشـطـة.
━━━━━━━━━━━━━━━
    """
    
    msg = bot.edit_message_text(
        instruction_text,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 إلغاء", callback_data="admin_panel")
        ),
        parse_mode="Markdown"
    )
    
    # الانتقال لخطوة استلام الآيدي
    bot.register_next_step_handler(msg, process_user_management_id)

def process_user_management_id(m):
    """التحقق من الآيدي وعرض خيارات التحكم بالمستخدم المختار"""
    target_id = m.text
    
    if not target_id.isdigit():
        bot.reply_to(m, "❌ خطأ! يجب إرسال الآيدي كأرقام فقط.")
        return
        
    user_info = get_user(int(target_id))
    
    if not user_info:
        bot.reply_to(m, "❌ هذا المستخدم غير موجود في قاعدة بيانات البوت.")
        return
        
    status_label = "🔴 محظور" if user_info['is_banned'] == 1 else "🟢 نشط"
    
    control_panel = f"""
👤 **مـلـف الـمـسـتـخـدم:**
━━━━━━━━━━━━━━━
🆔 الآيـدي: `{user_info['user_id']}`
👤 اليوزر: @{user_info['username'] if user_info['username'] else 'لا يوجد'}
💰 الرصيد: `{user_info['points']}` نقطة
📊 الحالة: `{status_label}`
📅 انضم في: `{user_info['join_date']}`
━━━━━━━━━━━━━━━
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # أزرار التحكم في حالة المستخدم
    if user_info['is_banned'] == 0:
        btn_ban = types.InlineKeyboardButton("🚫 حـظـر", callback_data=f"user_ban_{target_id}")
    else:
        btn_ban = types.InlineKeyboardButton("✅ فـك حـظـر", callback_data=f"user_unban_{target_id}")
        
    btn_add_pts = types.InlineKeyboardButton("➕ إضـافـة نـقـاط", callback_data=f"user_addpts_{target_id}")
    btn_rem_pts = types.InlineKeyboardButton("➖ خـصـم نـقـاط", callback_data=f"user_rempts_{target_id}")
    btn_back = types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_manage_users")
    
    markup.add(btn_ban)
    markup.add(btn_add_pts, btn_rem_pts)
    markup.add(btn_back)
    
    bot.send_message(
        m.chat.id, 
        control_panel, 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# ⚡ تـنـفـيذ عـمـلـيـات الـحـظـر والـتـقـاط
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data.startswith(("user_ban_", "user_unban_")))
def toggle_user_ban_status(c):
    """تغيير حالة الحظر للمستخدم في قاعدة البيانات"""
    action = "ban" if "user_ban_" in c.data else "unban"
    target_uid = c.data.replace(f"user_{action}_", "")
    
    new_status = 1 if action == "ban" else 0
    
    conn = get_db_connection()
    conn.execute(
        'UPDATE users SET is_banned = ? WHERE user_id = ?',
        (new_status, target_uid)
    )
    conn.commit()
    conn.close()
    
    alert_msg = "🚫 تم حظر المستخدم بنجاح!" if action == "ban" else "✅ تم فك الحظر بنجاح!"
    bot.answer_callback_query(c.id, alert_msg, show_alert=True)
    
    # تحديث اللوحة الحالية
    bot.delete_message(c.message.chat.id, c.message.message_id)

# ----------------------------------------------------------
# 📢 نـظـام الإذاعـة الـجـمـاعـيـة (Broadcast System)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast")
def start_broadcast_session(c):
    """بدء عملية إرسال رسالة لجميع مستخدمي البوت"""
    prompt = """
📢 **إرسـال إذاعـة عـامـة:**
━━━━━━━━━━━━━━━
• سيتم إرسال رسالتك لجميع المستخدمين.
• يمكنك إرسال (نص، صورة، أو ملف).
━━━━━━━━━━━━━━━
*أرسل الرسالة الآن أو أرسل 'إلغاء'*
    """
    msg = bot.edit_message_text(
        prompt,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 تراجع", callback_data="admin_panel")
        ),
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, perform_mass_broadcast)

def perform_mass_broadcast(m):
    """إرسال الرسالة لجميع اليوزرات المسجلين في الـ Database"""
    if m.text == "إلغاء":
        bot.reply_to(m, "❌ تم إلغاء الإذاعة.")
        return
        
    conn = get_db_connection()
    all_users = conn.execute('SELECT user_id FROM users').fetchall()
    conn.close()
    
    total = len(all_users)
    success = 0
    failed = 0
    
    progress_msg = bot.send_message(m.chat.id, f"🚀 جاري الإرسال لـ {total} مستخدم...")
    
    for user in all_users:
        try:
            # استخدام copy_message لضمان إرسال أي نوع من الوسائط
            bot.copy_message(
                chat_id=user['user_id'],
                from_chat_id=m.chat.id,
                message_id=m.message_id
            )
            success += 1
            time.sleep(0.05) # تأخير بسيط لتجنب حظر التليجرام (Flood)
        except:
            failed += 1
            
    summary = f"""
✅ **اكـتـمـلـت الإذاعـة:**
━━━━━━━━━━━━━━━
🟢 نـجـاح: `{success}`
🔴 فـشـل (حظر البوت): `{failed}`
📊 الإجـمـالـي: `{total}`
━━━━━━━━━━━━━━━
    """
    bot.edit_message_text(summary, m.chat.id, progress_msg.message_id, parse_mode="Markdown")

# ----------------------------------------------------------
# 🎫 تـفـعـيـل أكـواد الـهـدايا (Redeem Codes)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "redeem_gift")
def start_redeem_process(c):
    """طلب الكود من المستخدم لتزويد رصيده"""
    bot.edit_message_text(
        "🎟 **يرجى إرسال كود الهدية الخاص بك:**",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 رجوع", callback_data="wallet_info")
        )
    )
    bot.register_next_step_handler(c.message, validate_gift_code)

def validate_gift_code(m):
    """التحقق من صحة الكود في قاعدة البيانات وشحن الرصيد"""
    code_input = m.text.strip()
    
    conn = get_db_connection()
    code_data = conn.execute(
        'SELECT * FROM gift_codes WHERE code = ? AND status = "unused"',
        (code_input,)
    ).fetchone()
    
    if not code_data:
        bot.reply_to(m, "❌ الكود غير صحيح أو تم استخدامه مسبقاً.")
        conn.close()
        return
        
    # تحديث النقاط وحالة الكود
    points_to_give = code_data['points']
    
    conn.execute(
        'UPDATE users SET points = points + ? WHERE user_id = ?',
        (points_to_give, m.from_user.id)
    )
    conn.execute(
        'UPDATE gift_codes SET status = "used" WHERE id = ?',
        (code_data['id'],)
    )
    conn.commit()
    conn.close()
    
    bot.reply_to(
        m, 
        f"✅ **تم الشحن بنجاح!**\n💰 تمت إضافة `{points_to_give}` نقطة إلى حسابك."
    )

# نهاية الجزء الرابع (الأسطر 901-1200 فعلياً في Visual Studio)
# ..........................................................
# ----------------------------------------------------------
# 🕰️ نـظـام الـتـنـظـيـف الـتـلـقـائي (Auto-Cleaner System)
# ----------------------------------------------------------

def background_expiry_checker():
    """
    هذه الوظيفة تعمل كخادم خلفي (Daemon) لفحص تواريخ انتهاء البوتات.
    في حال انتهاء المدة، يقوم النظام بقتل العملية وحذف الملفات فوراً.
    """
    while True:
        try:
            # فتح اتصال جديد بقاعدة البيانات لهذا الخيط (Thread)
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # جلب جميع البوتات التي انتهت مدتها
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            expired_bots = cursor.execute(
                'SELECT * FROM active_bots WHERE expiry_time <= ?',
                (current_time,)
            ).fetchall()
            
            for bot_entry in expired_bots:
                # 1. إنهاء العملية (PID)
                pid = bot_entry['process_id']
                if pid != 0:
                    try:
                        p = psutil.Process(pid)
                        p.terminate() # إرسال أمر إيقاف
                        logging.info(f"Terminated expired bot: {pid}")
                    except psutil.NoSuchProcess:
                        pass
                
                # 2. حذف المجلد والملفات لضمان توفير مساحة السيرفر
                user_folder = os.path.dirname(bot_entry['file_path'])
                if os.path.exists(user_folder):
                    shutil.rmtree(user_folder)
                
                # 3. إرسال إشعار للمستخدم بانتهاء اشتراكه
                try:
                    bot.send_message(
                        bot_entry['user_id'],
                        "🚨 **إشعار انـتـهـاء:**\n\nلقد انتهت مدة استضافة بوتك وتم حذفه تلقائياً.\nيمكنك الشحن وإعادة التنصيب مرة أخرى."
                    )
                except:
                    pass
                
                # 4. مسح السجل من قاعدة البيانات
                cursor.execute(
                    'DELETE FROM active_bots WHERE id = ?',
                    (bot_entry['id'],)
                )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error in Watchdog: {e}")
            
        # الفحص يتم كل ساعة لتقليل الضغط على المعالج
        time.sleep(3600)

# تشغيل المراقب في خيط مستقل عند تشغيل الكود
threading.Thread(target=background_expiry_checker, daemon=True).start()

# ----------------------------------------------------------
# 🛠️ نـظـام الـدعم الـفـنـي (Support Ticket System)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "support_center")
def support_menu_display(c):
    """عرض واجهة التواصل مع إدارة بلاك تيك"""
    support_text = """
👨‍💻 **قـسـم الـدعم الـفـنـي:**
━━━━━━━━━━━━━━━
إذا واجهت مشكلة في التنصيب أو تريد استفساراً، 
أرسل رسالتك وسيرد عليك الأدمن في أقرب وقت.
━━━━━━━━━━━━━━━
    """
    markup = types.InlineKeyboardMarkup()
    btn_msg = types.InlineKeyboardButton("📝 إرسـال رسـالـة لـلأدمـن", callback_data="contact_admin")
    btn_back = types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")
    
    markup.add(btn_msg)
    markup.add(btn_back)
    
    bot.edit_message_text(
        support_text,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "contact_admin")
def contact_admin_step1(c):
    """تجهيز البوت لاستقبال رسالة الدعم من المستخدم"""
    msg = bot.edit_message_text(
        "✍️ **أكتب رسالتك الآن (نص فقط):**",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("❌ إلغاء", callback_data="support_center")
        )
    )
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(m):
    """توجيه الرسالة للأدمن مع إضافة أزرار الرد السريع"""
    if not m.text:
        bot.reply_to(m, "❌ يرجى إرسال نص فقط.")
        return
        
    user_id = m.from_user.id
    user_name = m.from_user.first_name
    
    admin_notif = f"""
📩 **رسـالـة دعم جـديـدة:**
━━━━━━━━━━━━━━━
👤 من: {user_name} (`{user_id}`)
💬 الرسالة:
_{m.text}_
━━━━━━━━━━━━━━━
    """
    
    # أزرار الرد السريع للأدمن
    markup = types.InlineKeyboardMarkup()
    reply_btn = types.InlineKeyboardButton("↪️ رد عـلـى الـمـسـتـخـدم", callback_data=f"reply_user_{user_id}")
    markup.add(reply_btn)
    
    bot.send_message(ADMIN_ID, admin_notif, reply_markup=markup, parse_mode="Markdown")
    bot.reply_to(m, "✅ تم إرسال رسالتك للأدمن، انتظر الرد.")

# ----------------------------------------------------------
# ↩️ نـظـام الـرد عـلـى الـمـسـتـخـدمـيـن
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_user_"))
def admin_reply_prompt(c):
    """دالة تمكن الأدمن من الرد مباشرة على صاحب الرسالة"""
    target_uid = c.data.replace("reply_user_", "")
    
    msg = bot.send_message(
        c.message.chat.id, 
        f"📝 **أكتب ردك على المستخدم `{target_uid}`:**"
    )
    bot.register_next_step_handler(msg, lambda m: execute_admin_reply(m, target_uid))

def execute_admin_reply(m, target_id):
    """إرسال رد الأدمن إلى المستخدم النهائي"""
    reply_text = m.text
    
    try:
        final_msg = f"""
👨‍💻 **رد مـن الإدارة:**
━━━━━━━━━━━━━━━
_{reply_text}_
━━━━━━━━━━━━━━━
        """
        bot.send_message(target_id, final_msg, parse_mode="Markdown")
        bot.reply_to(m, "✅ تم إرسال الرد بنجاح.")
    except Exception as e:
        bot.reply_to(m, f"❌ فشل الإرسال: {e}")

# ----------------------------------------------------------
# 🔍 فـحص جـودة الـبـوت (Health Check Route)
# ----------------------------------------------------------

def get_total_storage_used():
    """حساب المساحة الإجمالية المستهلكة من قبل بوتات المستخدمين"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(UPLOAD_FOLDER):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    
    # تحويل من بايت إلى ميجابايت
    return round(total_size / (1024 * 1024), 2)

# نهاية الجزء الخامس (الأسطر 1201-1500 فعلياً في Visual Studio)
# ..........................................................
# ----------------------------------------------------------
# 📢 نـظـام الاشـتـراك الإجـبـاري الـمـطـور (Enhanced Force Join)
# ----------------------------------------------------------

def check_is_member(user_id):
    """
    هذه الوظيفة تتحقق من انضمام المستخدم لقناة التليجرام الخاصة بك.
    تم تصميمها لتكون سريعة ولا تسبب تعليق للبوت (Non-blocking).
    """
    # استثناء المطور (الأدمن) من فحص الاشتراك لضمان الوصول الدائم
    if user_id == ADMIN_ID:
        return True
        
    try:
        # استخدام API التليجرام الرسمي للتحقق من العضوية
        member_status = bot.get_chat_member(DEVELOPER_CHANNEL, user_id).status
        
        # الحالات المسموح لها باستخدام البوت
        allowed_statuses = ['member', 'administrator', 'creator']
        
        if member_status in allowed_statuses:
            return True
        else:
            return False
            
    except Exception as error:
        # في حال وجود خطأ (مثل أن البوت ليس أدمن في القناة)، نسمح بالمرور مؤقتاً
        logging.error(f"Force Join Error: {error}")
        return True

@bot.callback_query_handler(func=lambda c: c.data == "verify_subscription")
def verify_sub_callback(c):
    """معالج زر 'تم الاشتراك' لتحديث حالة المستخدم"""
    user_id = c.from_user.id
    
    if check_is_member(user_id):
        bot.answer_callback_query(c.id, "✅ شـكـراً لـك! تـم الـتـأكـد مـن انـضـمـامـك.")
        # مسح رسالة التحذير وإرسال القائمة الرئيسية
        bot.delete_message(c.message.chat.id, c.message.message_id)
        # استدعاء دالة البداية (Start)
        class MockMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = from_user
        
        start_command_handler(MockMessage(c.message.chat.id, c.from_user))
    else:
        bot.answer_callback_query(
            c.id, 
            "❌ عـذراً! أنـت لـم تـنـضـم لـلـقـنـاة بـعـد.", 
            show_alert=True
        )

# ----------------------------------------------------------
# 🛡️ نـظـام فـحـص سـلامـة الـمـلـف (Code Security Guard)
# ----------------------------------------------------------

def is_code_safe(file_content):
    """
    فحص محتوى ملف البايثون المرفوع قبل إرساله للأدمن.
    يتم البحث عن كلمات مفتاحية خبيثة قد تستهدف ملفات النظام.
    """
    # تحويل المحتوى إلى نص للبحث فيه
    content_str = file_content.decode('utf-8', errors='ignore').lower()
    
    # قائمة بالكلمات المحظورة (Blacklist) التي تشكل خطراً على السيرفر
    dangerous_keywords = [
        'os.remove', 'os.rmdir', 'shutil.rmtree', 
        'subprocess.call(["rm"', 'mkfs', 'os.system("rm',
        'format c:', 'chmod 777', '/etc/shadow', 
        'import pty', 'os.setuid'
    ]
    
    # البحث عن أي تطابق
    for keyword in dangerous_keywords:
        if keyword in content_str:
            return False, keyword
            
    return True, None

# ----------------------------------------------------------
# ⚙️ مـعـالـج الـرفـع الـمـقـيـد (Restricted Upload Handler)
# ----------------------------------------------------------

def handle_secure_upload(message):
    """
    هذه الوظيفة تحل محل عملية الرفع التقليدية لضمان أقصى حماية.
    تجمع بين فحص الاشتراك وفحص محتوى الملف.
    """
    user_id = message.from_user.id
    
    # 1. التأكد من الاشتراك الإجباري أولاً
    if not check_is_member(user_id):
        sub_markup = types.InlineKeyboardMarkup()
        sub_markup.add(types.InlineKeyboardButton("📢 انـضـم لـلـقـنـاة", url=f"https://t.me/{DEVELOPER_CHANNEL.replace('@','')}"))
        sub_markup.add(types.InlineKeyboardButton("✅ تـم الاشـتـراك", callback_data="verify_subscription"))
        
        bot.reply_to(
            message,
            "⚠️ **تـنـبـيـه:** يـجـب عـلـيـك الانـضـمـام لـقـنـاة الـمـطـور أولاً لـتـتـمـكـن مـن الـتـنـصـيـب.",
            reply_markup=sub_markup
        )
        return

    # 2. فحص نوع الملف المرفوع
    if not message.document or not message.document.file_name.endswith('.py'):
        bot.reply_to(message, "❌ يرجى إرسال ملف بصيغة .py فقط!")
        return

    # 3. تحميل الملف لفحصه برمجياً قبل الحفظ
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # إجراء الفحص الأمني
    safe, threat = is_code_safe(downloaded_file)
    
    if not safe:
        # إشعار المستخدم بالرفض الأمني
        bot.reply_to(
            message, 
            f"🚫 **تـم رفـض الـمـلـف!**\n\nتـم اكتشاف كود مشبوه: `{threat}`\nنـحـن لا نـسـمـح بـالـمـلـفـات الـتـي تـحـاول الـتـلاعب بـمـلـفات الـنـظام."
        )
        # إشعار الأدمن بمحاولة رفع ملف خبيث
        bot.send_message(
            ADMIN_ID, 
            f"⚠️ **تـنـبـيـه أمـنـي:**\nالمستخدم `{user_id}` حاول رفع ملف يحتوي على `{threat}`."
        )
        return

    # إذا مر الملف من الفحص، ننتقل لمرحلة تحديد الأيام (كما في الأجزاء السابقة)
    # [تكملة منطق الحفظ هنا...]
    save_file_to_waiting_area(message)

# ----------------------------------------------------------
# 📋 إعـدادات الـنـظـام (System Settings)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "admin_settings")
def admin_settings_menu(c):
    """لوحة تحكم فرعية للأدمن لتعديل إعدادات البوت برمجياً"""
    if c.from_user.id != ADMIN_ID:
        return
        
    settings_txt = """
⚙️ **إعـدادات الـنـظـام الـتـقـنـيـة:**
━━━━━━━━━━━━━━━
تـحـكـم فـي خـصـائص الـتـنـصـيـب:
━━━━━━━━━━━━━━━
    """
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # أزرار لتغيير الإعدادات (كمثال)
    btn_toggle_sub = types.InlineKeyboardButton("🔔 تفعيل/تعطيل الاشتراك الإجباري", callback_data="toggle_force_join")
    btn_cleanup = types.InlineKeyboardButton("🧹 تنظيف المجلدات المؤقتة", callback_data="manual_cleanup")
    btn_back = types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")
    
    markup.add(btn_toggle_sub, btn_cleanup, btn_back)
    
    bot.edit_message_text(
        settings_txt,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# نهاية الجزء السادس (الأسطر 1501-1800 فعلياً في Visual Studio)
# ..........................................................
# ----------------------------------------------------------
# 💸 نـظـام تـحـويـل الـنـقـاط الآمـن (Secure Points Transfer)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "transfer_points")
def start_transfer_points_process(c):
    """
    الدالة المسؤولة عن بدء عملية نقل النقاط من مستخدم إلى آخر.
    تم تصميمها لتطلب الآيدي ثم الكمية مع فحص الرصيد.
    """
    user_id = c.from_user.id
    current_balance = get_points(user_id)
    
    if current_balance < 10:
        bot.answer_callback_query(
            c.id, 
            "⚠️ عذراً! يجب أن يكون رصيدك 10 نقاط على الأقل للتحويل.", 
            show_alert=True
        )
        return

    instruction = f"""
💰 **نـظـام تـحـويـل الـنـقـاط:**
━━━━━━━━━━━━━━━
رصيدك الحالي: `{current_balance}` نقطة.
━━━━━━━━━━━━━━━
يرجى إرسال **آيـدي (ID)** الشخص المراد التحويل له:
    """
    
    msg = bot.edit_message_text(
        instruction,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 إلغاء", callback_data="wallet_info")
        ),
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_transfer_recipient_id)

def process_transfer_recipient_id(m):
    """التحقق من آيدي المستلم وصلاحيته قبل طلب الكمية"""
    recipient_id = m.text
    
    if not recipient_id.isdigit():
        bot.reply_to(m, "❌ خطأ! الآيدي يجب أن يتكون من أرقام فقط.")
        return
        
    recipient_id = int(recipient_id)
    
    # منع المستخدم من التحويل لنفسه
    if recipient_id == m.from_user.id:
        bot.reply_to(m, "❌ لا يمكنك تحويل النقاط لنفسك!")
        return
        
    recipient_data = get_user(recipient_id)
    if not recipient_data:
        bot.reply_to(m, "❌ هذا المستخدم غير مسجل في البوت.")
        return
        
    msg = bot.reply_to(
        m, 
        f"✅ تم العثور على `{recipient_id}`.\nأرسل الآن **كمية النقاط** المراد تحويلها:"
    )
    bot.register_next_step_handler(msg, lambda message: finalize_points_transfer(message, recipient_id))

def finalize_points_transfer(m, to_id):
    """تفيذ العملية المالية وتحديث قاعدة البيانات للطرفين"""
    if not m.text.isdigit():
        bot.reply_to(m, "❌ يرجى إرسال أرقام فقط.")
        return
        
    amount = int(m.text)
    sender_id = m.from_user.id
    sender_balance = get_points(sender_id)
    
    if amount < 5:
        bot.reply_to(m, "❌ الحد الأدنى للتحويل هو 5 نقاط.")
        return
        
    if sender_balance < amount:
        bot.reply_to(m, "❌ رصيدك لا يكفي! رصيدك الحالي هو: " + str(sender_balance))
        return
        
    # تنفيذ عملية النقل (Atomically)
    conn = get_db_connection()
    try:
        # خصم من المرسل
        conn.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (amount, sender_id))
        # إضافة للمستلم
        conn.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (amount, to_id))
        conn.commit()
        
        # إشعار الطرفين
        bot.reply_to(m, f"✅ تم تحويل `{amount}` نقطة بنجاح إلى `{to_id}`.")
        bot.send_message(
            to_id, 
            f"💰 **وصلك تحويل جديد!**\nالكمية: `{amount}` نقطة\nمن: `{sender_id}`"
        )
    except Exception as e:
        bot.reply_to(m, f"❌ حدث خطأ فني أثناء التحويل: {e}")
    finally:
        conn.close()

# ----------------------------------------------------------
# 🎟️ نـظـام الأكـواد الـتـرويـجـيـة (Promo Codes System)
# ----------------------------------------------------------

def create_promo_code_table():
    """إنشاء جدول الأكواد التي تدعم تعدد الاستخدام"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            points INTEGER,
            max_uses INTEGER,
            current_uses INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

create_promo_code_table()

@bot.callback_query_handler(func=lambda c: c.data == "admin_gen_promo")
def admin_promo_step1(c):
    """بداية إنشاء كود ترويجي (للأدمن فقط)"""
    if c.from_user.id != ADMIN_ID: return
    
    msg = bot.edit_message_text(
        "🎫 **أرسل بيانات الكود بالتنسيق التالي:**\n`الكود-النقاط-عدد_الاستخدامات`\n\nمثال: `FREE50-50-10`",
        c.message.chat.id,
        c.message.message_id
    )
    bot.register_next_step_handler(msg, save_promo_code_logic)

def save_promo_code_logic(m):
    """تحليل النص وحفظ الكود الترويجي الجديد"""
    try:
        data = m.text.split('-')
        code_str = data[0].upper()
        pts = int(data[1])
        uses = int(data[2])
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO promo_codes (code, points, max_uses) VALUES (?, ?, ?)',
            (code_str, pts, uses)
        )
        conn.commit()
        conn.close()
        
        bot.reply_to(m, f"✅ تم إنشاء كود ترويجي: `{code_str}`\nيعطي `{pts}` نقطة لـ `{uses}` مستخدم.")
    except Exception as e:
        bot.reply_to(m, "❌ خطأ في التنسيق! تأكد من استخدام الـ `-` بشكل صحيح.")

# ----------------------------------------------------------
# 🛡️ حـمـايـة مـن تـكـرار الـنـقـر (Anti-Spam Click)
# ----------------------------------------------------------

user_last_click = {}

def is_spamming(user_id):
    """منع المستخدم من الضغط على الأزرار بسرعة جنونية"""
    now = time.time()
    if user_id in user_last_click:
        if now - user_last_click[user_id] < 0.8: # أقل من ثانية
            return True
    user_last_click[user_id] = now
    return False

# نهاية الجزء السابع (الأسطر 1801-2100 فعلياً في Visual Studio)
# ..........................................................
# ----------------------------------------------------------
# 💾 نـظـام الـنـسـخ الاحـتـيـاطـي الـتلقائي (Daily Auto-Backup)
# ----------------------------------------------------------

def send_database_backup():
    """
    وظيفة مبرمجة لترسل نسخة من قاعدة البيانات (titan_v37.db)
    إلى حساب الأدمن الخاص بك كل 24 ساعة لضمان عدم فقدان البيانات.
    """
    while True:
        try:
            # الانتظار لمدة 24 ساعة (86400 ثانية)
            time.sleep(86400)
            
            # التأكد من وجود ملف قاعدة البيانات
            if os.path.exists(DB_PATH):
                with open(DB_PATH, 'rb') as db_file:
                    caption = f"📦 **نسخة احتياطية لقاعدة البيانات**\n📅 التاريخ: `{datetime.now().strftime('%Y-%m-%d')}`\n🤖 نظام تايتان V37"
                    
                    bot.send_document(
                        ADMIN_ID, 
                        db_file, 
                        caption=caption, 
                        parse_mode="Markdown"
                    )
                logging.info("Backup sent successfully to Admin.")
        except Exception as e:
            logging.error(f"Backup Error: {e}")

# تشغيل خيط النسخ الاحتياطي في الخلفية
threading.Thread(target=send_database_backup, daemon=True).start()

# ----------------------------------------------------------
# 🤖 واجـهـة "بـوتـاتـي الـنـشـطـة" (User Bot Management)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "my_active_bots")
def show_user_hosted_bots(c):
    """
    عرض قائمة بالاستضافات التي يملكها المستخدم حالياً مع حالتها.
    تم تصميم الواجهة بأسلوب القوائم لتسهيل التنقل.
    """
    uid = c.from_user.id
    
    conn = get_db_connection()
    user_bots = conn.execute(
        'SELECT * FROM active_bots WHERE user_id = ?', 
        (uid,)
    ).fetchall()
    conn.close()
    
    if not user_bots:
        bot.answer_callback_query(
            c.id, 
            "❌ ليس لديك أي استضافات نشطة حالياً.", 
            show_alert=True
        )
        return

    txt = "🤖 **قـائـمـة اسـتـضـافاتـك الـنـشـطـة:**\n"
    txt += "━━━━━━━━━━━━━━━\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for b in user_bots:
        # تحديد رمز الحالة (شغال أو متوقف)
        status_icon = "🟢" if b['status'] == "running" else "🔴"
        btn_label = f"{status_icon} | {b['bot_name']}"
        
        markup.add(
            types.InlineKeyboardButton(
                btn_label, 
                callback_data=f"manage_my_bot_{b['id']}"
            )
        )
    
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start"))
    
    bot.edit_message_text(
        txt,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# ⚙️ لـوحـة الـتـحـكـم الـفـردية لـلـبـوت (Individual Bot Controls)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("manage_my_bot_"))
def manage_single_bot_panel(c):
    """لوحة تحكم فرعية لكل بوت تتيح (إيقاف، إعادة تشغيل، حذف)"""
    bot_db_id = c.data.replace("manage_my_bot_", "")
    
    conn = get_db_connection()
    b_data = conn.execute(
        'SELECT * FROM active_bots WHERE id = ?', 
        (bot_db_id,)
    ).fetchone()
    conn.close()
    
    if not b_data:
        bot.answer_callback_query(c.id, "❌ خطأ في جلب بيانات البوت.")
        return

    # حساب الوقت المتبقي
    expiry = datetime.strptime(b_data['expiry_time'], '%Y-%m-%d %H:%M:%S')
    time_left = expiry - datetime.now()
    days_left = time_left.days
    
    status_text = "🟢 يعمل الآن" if b_data['status'] == "running" else "🔴 متوقف"
    
    panel_txt = f"""
⚙️ **إدارة الـبـوت:** `{b_data['bot_name']}`
━━━━━━━━━━━━━━━
📊 الـحـالـة: `{status_text}`
🆔 الـعـمـلـيـة (PID): `{b_data['process_id']}`
⏳ الـمـدة الـمـتـبـقـيـة: `{days_left}` يوم
📅 الانـتـهـاء: `{b_data['expiry_time']}`
━━━━━━━━━━━━━━━
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_restart = types.InlineKeyboardButton("♻️ إعـادة تـشـغـيـل", callback_data=f"bot_restart_{bot_db_id}")
    btn_stop = types.InlineKeyboardButton("🛑 إيـقـاف مـؤقـت", callback_data=f"bot_stop_{bot_db_id}")
    btn_del = types.InlineKeyboardButton("🗑️ حـذف نـهـائي", callback_data=f"bot_delete_{bot_db_id}")
    btn_back = types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="my_active_bots")
    
    markup.add(btn_restart, btn_stop)
    markup.add(btn_del)
    markup.add(btn_back)
    
    bot.edit_message_text(
        panel_txt,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ----------------------------------------------------------
# 🔄 دوال الـتـنـفـيذ الـمـادي (Physical Execution Logic)
# ----------------------------------------------------------

def kill_bot_process(pid):
    """محاولة إنهاء العملية برمجياً باستخدام PID"""
    try:
        process = psutil.Process(pid)
        process.terminate() # محاولة الإيقاف اللطيف
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

@bot.callback_query_handler(func=lambda c: c.data.startswith("bot_stop_"))
def user_stop_bot_logic(c):
    """إيقاف البوت وتحديث الحالة في قاعدة البيانات"""
    bot_id = c.data.replace("bot_stop_", "")
    conn = get_db_connection()
    b = conn.execute('SELECT * FROM active_bots WHERE id = ?', (bot_id,)).fetchone()
    
    if b and b['status'] == "running":
        kill_bot_process(b['process_id'])
        conn.execute('UPDATE active_bots SET status = "stopped", process_id = 0 WHERE id = ?', (bot_id,))
        conn.commit()
        bot.answer_callback_query(c.id, "🛑 تم إيقاف البوت بنجاح.")
        manage_single_bot_panel(c) # تحديث الواجهة
    else:
        bot.answer_callback_query(c.id, "⚠️ البوت متوقف بالفعل.")
    conn.close()

# نهاية الجزء الثامن (الأسطر 2101-2400 فعلياً في Visual Studio)
# ..........................................................
# ----------------------------------------------------------
# 📝 نـظـام سـجـلات الـنـظـام الـمـركـزي (Admin System Logs)
# ----------------------------------------------------------

def log_admin_event(event_type, details):
    """
    وظيفة مخصصة لإرسال إشعارات فورية للأدمن عند حدوث أي عملية 
    مهمة داخل البوت (شحن، تحويل، تنصيب، حذف).
    """
    log_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_msg = f"""
🔔 **سـجـل الـنـظـام الـجـديـد:**
━━━━━━━━━━━━━━━
 نوع الحدث: `{event_type}`
 التوقيت: `{log_time}`
 التفاصيل: 
_{details}_
━━━━━━━━━━━━━━━
    """
    try:
        # إرسال السجل إلى الأدمن في قناة خاصة أو في الخاص
        bot.send_message(ADMIN_ID, log_msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Logging Error: {e}")

# ----------------------------------------------------------
# 📊 تـطـويـر لـوحـة الإحـصـائـيـات (Advanced Analytics)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "advanced_stats")
def show_advanced_system_stats(c):
    """
    لوحة إحصائيات عميقة للأدمن توضح استهلاك كل مستخدم للموارد
    وتعطي صورة كاملة عن حالة "الهارد وير".
    """
    if c.from_user.id != ADMIN_ID: return
    
    # حساب عدد العمليات النشطة فعلياً في النظام
    process_count = 0
    for proc in psutil.process_iter(['name']):
        if 'python' in proc.info['name'].lower():
            process_count += 1

    # جلب حجم قاعدة البيانات
    db_size = os.path.getsize(DB_PATH) / (1024 * 1024) # MB
    
    # جلب إحصائيات من الـ DB
    conn = get_db_connection()
    total_pts = conn.execute('SELECT SUM(points) FROM users').fetchone()[0] or 0
    total_bots = conn.execute('SELECT COUNT(*) FROM active_bots').fetchone()[0]
    conn.close()

    stats_txt = f"""
*📊 تـحـلـيـل أداء الـنـظـام الـشـامـل:*
━━━━━━━━━━━━━━━
*📁 حـجـم قـاعدة الـبـيانات:* `{db_size:.2f} MB`
*💰 إجمالي الـنـقـاط بالـسوق:* `{total_pts}`
*🤖 بوتات قيد الاستضافة:* `{total_bots}`
*⚙️ عـمليات Python الـنشطة:* `{process_count}`
━━━━━━━━━━━━━━━
*🖥️ استهلاك الذاكرة العشوائية:*
`{psutil.virtual_memory().percent}%` مستخدم من أصل `{psutil.virtual_memory().total / (1024**3):.1f} GB`
━━━━━━━━━━━━━━━
    """
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔄 تـحـديث الـبيـانات", callback_data="advanced_stats"))
    kb.add(types.InlineKeyboardButton("🔙 رجـوع", callback_data="admin_panel"))
    
    bot.edit_message_text(stats_txt, c.message.chat.id, c.message.message_id, reply_markup=kb, parse_mode="Markdown")

# ----------------------------------------------------------
# 🩺 نـظـام الـتـشـخـيـص والـإصـلاح (Auto-Healing System)
# ----------------------------------------------------------

def check_and_repair_zombie_processes():
    """
    وظيفة ذكية تبحث عن البوتات التي مسجلة كـ "تعمل" (Running) 
    في الـ DB لكن عمليتها (PID) توقفت فجأة في السيرفر.
    """
    while True:
        try:
            conn = get_db_connection()
            active_list = conn.execute('SELECT * FROM active_bots WHERE status = "running"').fetchall()
            
            for bot_record in active_list:
                pid = bot_record['process_id']
                
                # فحص هل الـ PID موجود فعلاً في السيرفر؟
                if not psutil.pid_exists(pid):
                    # إذا لم يوجد، نحدث الحالة إلى "متوقف" لتجنب التضليل
                    conn.execute(
                        'UPDATE active_bots SET status = "crashed", process_id = 0 WHERE id = ?',
                        (bot_record['id'],)
                    )
                    # إشعار الأدمن بالعطل
                    log_admin_event(
                        "⚠️ تـعـطـل بـوت تـلقـائي", 
                        f"البوت: `{bot_record['bot_name']}`\nللمستخدم: `{bot_record['user_id']}`\nتوقف عن العمل فجأة."
                    )
            
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Auto-Repair Error: {e}")
            
        # فحص كل 30 دقيقة
        time.sleep(1800)

# تشغيل نظام التشخيص في الخلفية
threading.Thread(target=check_and_repair_zombie_processes, daemon=True).start()

# ----------------------------------------------------------
# 📢 نـظـام الـإشـعارات لـلـمـسـتـخـدمـيـن (Global Alerts)
# ----------------------------------------------------------

@bot.callback_query_handler(func=lambda c: c.data == "admin_global_alert")
def global_alert_step1(c):
    """إرسال رسالة تنبيهية تظهر كـ (Alert) منبثق لكل المستخدمين عند دخولهم"""
    if c.from_user.id != ADMIN_ID: return
    
    msg = bot.send_message(c.message.chat.id, "✍️ **أرسل نص التنبيه المنبثق (قصير):**")
    bot.register_next_step_handler(msg, save_global_alert)

def save_global_alert(m):
    """حفظ التنبيه في ملف JSON ليظهر للجميع"""
    alert_data = {
        "text": m.text,
        "date": datetime.now().strftime('%Y-%m-%d')
    }
    with open('global_alert.json', 'w') as f:
        json.dump(alert_data, f)
    
    bot.reply_to(m, "✅ تم حفظ التنبيه العام. سيظهر لكل مستخدم يفتح القائمة الرئيسية.")

# ----------------------------------------------------------
# 🧹 تـنـظـيف الـملـفات الـتـالـفـة (Garbage Collector)
# ----------------------------------------------------------

def manual_system_cleanup():
    """حذف ملفات بايثون المؤقتة __pycache__ لتوفير مساحة"""
    count = 0
    for root, dirs, files in os.walk('.'):
        for d in dirs:
            if d == '__pycache__':
                shutil.rmtree(os.path.join(root, d))
                count += 1
    return count

@bot.callback_query_handler(func=lambda c: c.data == "manual_cleanup")
def cleanup_callback_handler(c):
    if c.from_user.id != ADMIN_ID: return
    
    removed = manual_system_cleanup()
    bot.answer_callback_query(c.id, f"🧹 تم تنظيف {removed} مجلدات مؤقتة!", show_alert=True)

# نهاية الجزء التاسع (الأسطر 2401-2700 فعلياً في Visual Studio)
# ..........................................................
# --------------------------------------------------------------------------
# 🔗 نـظـام الـتـحـقـق مـن الـمـكـتـبـات (Dependency Integrity Check)
# --------------------------------------------------------------------------

def verify_system_dependencies():
    """
    وظيفة اختيارية تتأكد من أن جميع المكتبات تعمل بكفاءة قبل الإقلاع.
    تساعد في تجنب أخطاء 'ImportError' أثناء التشغيل الطويل.
    """
    required_modules = ['telebot', 'psutil', 'sqlite3', 'requests']
    print("--- Checking System Core ---")
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"[🛡️] Module '{module}': Ready")
        except ImportError:
            print(f"[❌] Critical Error: Module '{module}' is missing!")
            return False
            
    return True

# --------------------------------------------------------------------------
# 🛠️ مـعـالـج الأخـطـاء الـشـامـل (Global Exception Recovery Layer)
# --------------------------------------------------------------------------

def titan_global_exception_handler(exctype, value, tb):
    """
    هذا هو 'الصندوق الأسود' للبوت. في حال حدوث خطأ برمجي (Runtime Error)، 
    بدلاً من توقف البوت، تقوم هذه الدالة بحجز الخطأ وإعادة تشغيل الخدمات.
    """
    import traceback
    
    # 1. تنسيق تفاصيل الخطأ بشكل احترافي
    error_header = "================ ERROR REPORT ================"
    error_trace = "".join(traceback.format_exception(exctype, value, tb))
    error_footer = "=============================================="
    
    # 2. بناء رسالة التحذير للأدمن
    full_report = (
        f"⚠️ **تـحـذير: انـهـيـار مـفـاجـئ فـي الـنـظـام!**\n\n"
        f"🆔 **النوع:** `{exctype.__name__}`\n"
        f"💬 **الرسالة:** `{value}`\n\n"
        f"🕒 **الـوقـت:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"📜 **تـتـبـع الـخـطأ:**\n"
        f"```python\n{error_trace[-800:]}\n```"
    )
    
    # 3. محاولة إخطار المطور (الأدمن)
    try:
        bot.send_message(ADMIN_ID, full_report, parse_mode="Markdown")
    except Exception as notify_err:
        print(f"Failed to notify admin: {notify_err}")

    # 4. حفظ الخطأ في سجل ملفات السيرفر للرجوع إليه
    try:
        with open("system_crash.log", "a", encoding="utf-8") as crash_file:
            crash_file.write(f"\n{error_header}\n")
            crash_file.write(f"Timestamp: {datetime.now()}\n")
            crash_file.write(error_trace)
            crash_file.write(f"{error_footer}\n")
    except:
        pass

    # 5. طباعة الخطأ في الكونسول (Visual Studio Terminal)
    sys.__excepthook__(exctype, value, tb)

# تفعيل المعالج ليكون هو المسؤول عن النظام بالكامل
sys.excepthook = titan_global_exception_handler

# --------------------------------------------------------------------------
# 🚀 مـحـرك الـتـشـغـيـل الـنـهـائـي (The Master Polling Engine)
# --------------------------------------------------------------------------

def launch_bot_main_loop():
    """
    تشغيل محرك استقبال الرسائل بنظام (Infinity Polling).
    هذه الدالة تضمن استمرارية البوت 24/7 دون توقف.
    """
    
    # مسح بيانات الشاشة لبداية نظيفة
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

    # شعار الترحيب الخاص بـ بلاك تيك (ASCII Art)
    black_tech_art = """
    ***********************************************************
    * *
    * 🛡️  TITAN HOSTING SYSTEM V37 - FULL EDITION  🛡️    *
    * 👨‍💻  DEVELOPER: @Alikhalafm                        *
    * 📢  CHANNEL: @teamofghost                         *
    * *
    ***********************************************************
    """
    print(black_tech_art)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] STATUS: Checking Database...")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] STATUS: Loading Admin Settings...")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] STATUS: Starting Background Watchdog...")
    
    try:
        # تصفير أي اتصالات قديمة مع سيرفرات تليجرام
        bot.remove_webhook()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ SUCCESS: Titan System is Online!")

        # التشغيل اللانهائي مع ضبط وقت الانتظار
        bot.infinity_polling(
            timeout=120, 
            long_polling_timeout=60,
            logger_level=logging.ERROR,
            allowed_updates=['message', 'callback_query', 'document']
        )
        
    except Exception as fatal_error:
        # في حالة فشل الاتصال بالإنترنت أو تعطل السيرفر
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 CRITICAL: {fatal_error}")
        print("🔄 Reconnecting in 10 seconds...")
        time.sleep(10)
        launch_bot_main_loop()

# --------------------------------------------------------------------------
# 🏁 نـقـطـة بـدايـة الـتـنـفـيـذ (Final Entry Point)
# --------------------------------------------------------------------------

if __name__ == "__main__":
    """
    هذه هي أول منطقة يتم تنفيذها عند تشغيل الملف.
    تقوم بتجهيز البيئة والتأكد من الملفات قبل إطلاق البوت.
    """
    
    # 1. التأكد من سلامة المكتبات
    if not verify_system_dependencies():
        print("❌ System check failed. Please install missing modules.")
        sys.exit(1)

    # 2. التأكد من وجود مجلدات البيانات
    required_paths = [UPLOAD_FOLDER, PENDING_FOLDER, 'backups']
    for path in required_paths:
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"📁 Initialized directory: {path}")

    # 3. اختبار قاعدة البيانات للمرة الأخيرة
    try:
        conn_test = sqlite3.connect(DB_PATH)
        conn_test.execute('SELECT 1')
        conn_test.close()
        print("🗄️ Database: Connection Established.")
    except Exception as e:
        print(f"🗄️ Database: Error {e}")
        sys.exit(1)

    # 4. إطلاق المحرك الرئيسي
    launch_bot_main_loop()

# ==========================================================================
# ✅ تـم اكـتـمـال بـرمـجـة نـظـام تـايـتـان V37 بـحـمـد الله
# 🛡️ إجـمـالـي الـتـوقـع بـعـد الـتـجـمـيـع: 3000 سـطـر بـنـسـيـق Visual Studio.
# 👨‍💻 جـمـيـع الـحـقـوق مـحـفـوظـة لـدى @teamofghost
# ==========================================================================




# =====================================================
# ADDITION: PROJECTS BUTTON + MULTI-HOSTING SUPPORT
# (No filtering, original code untouched)
# =====================================================

try:
    from telebot import types
except Exception:
    pass

# ---- Safe helpers (do not override existing ones) ----
def __get_ip_safe__():
    try:
        return get_network_ip()
    except Exception:
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

# ---- Multi-hosting storage (non-invasive) ----
# Uses existing DB_CTRL if present; otherwise uses in-memory fallback.
__PROJECTS_FALLBACK__ = {}

def __add_project_fallback__(uid, file_name, raw_url, api_token):
    __PROJECTS_FALLBACK__.setdefault(uid, []).append({
        "file_name": file_name,
        "raw_url": raw_url,
        "api_token": api_token,
        "is_active": True
    })

def __get_projects_fallback__(uid):
    return __PROJECTS_FALLBACK__.get(uid, [])

# ---- Projects button (exact format requested) ----
@bot.message_handler(func=lambda m: "مشاريعي" in m.text)
def __projects_button__(msg):
    uid = msg.from_user.id

    projects = []
    try:
        projects = DB_CTRL.get_user_projects(uid)
    except Exception:
        projects = __get_projects_fallback__(uid)

    if not projects:
        bot.send_message(msg.chat.id, "📁 لا توجد مشاريع حالياً")
        return

    ip = __get_ip_safe__()

    for p in projects:
        file_name = p.get("file_name", "tool.py")
        raw_url = p.get("raw_url", "http://server.local/tool.py")
        token = p.get("api_token", "ABC123")
        status = "مفعل"

        text = (
            f"📁 {file_name}\n\n"
            f"🔗 رابط العرض:\n"
            f"{raw_url}\n\n"
            f"🚀 رابط التشغيل:\n"
            f"http://{ip}:5000/run?token={token}\n\n"
            f"🔑 API TOKEN:\n"
            f"{token}\n\n"
            f"✅ الحالة: {status}"
        )
        bot.send_message(msg.chat.id, text)

# ---- Allow adding multiple hostings at once (batch-safe) ----
# Accepts multiple lines: file.py|http://url
@bot.message_handler(func=lambda m: "|" in m.text and "\n" in m.text)
def __batch_add_projects__(msg):
    uid = msg.from_user.id
    lines = [l for l in msg.text.splitlines() if "|" in l]
    added = 0
    for line in lines:
        try:
            name, url = line.split("|", 1)
            try:
                token = DB_CTRL.add_project(uid, name.strip(), url.strip()) # type: ignore
            except Exception:
                import uuid
                token = uuid.uuid4().hex[:12].upper()
                __add_project_fallback__(uid, name.strip(), url.strip(), token)
            added += 1
        except Exception:
            continue
    if added:
        bot.send_message(msg.chat.id, f"✅ تم إضافة {added} استضافة بنجاح")

# ---- Single add fallback (keeps existing behavior intact) ----
@bot.message_handler(func=lambda m: "|" in m.text and "\n" not in m.text)
def __single_add_project__(msg):
    uid = msg.from_user.id
    try:
        name, url = msg.text.split("|", 1)
        try:
            token = DB_CTRL.add_project(uid, name.strip(), url.strip()) # type: ignore
        except Exception:
            import uuid
            token = uuid.uuid4().hex[:12].upper()
            __add_project_fallback__(uid, name.strip(), url.strip(), token)
        bot.send_message(msg.chat.id, f"✅ تمت الإضافة\nTOKEN: {token}")
    except Exception:
        pass

# =====================================================
# END ADDITION
# =====================================================

@bot.message_handler(func=lambda m: m.text == "📁 مشاريعي")
def open_projects_from_keyboard(m):
    class MockCallback:
        def __init__(self, message):
            self.from_user = message.from_user
            self.message = message
            self.id = None
    show_user_hosted_bots(MockCallback(m))
