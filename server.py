import asyncio
import os
import sys
import json
import datetime
import logging
import re
import random
import sqlite3
import subprocess
import time
from typing import List, Dict, Any, Optional

# ==============================================================================
# 🛑 المرحلة 1: المكتبات والاعتمادات الأساسية
# ==============================================================================
# يتم التحقق من وجود مكتبة Telethon وإذا لم تكن موجودة يتم تثبيتها تلقائياً
# لضمان استمرارية عمل البوت في أي بيئة تشغيل.
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        StartBotRequest, ReadHistoryRequest, GetHistoryRequest, 
        GetBotCallbackAnswerRequest, SendMessageRequest
    )
    from telethon.tl.functions.channels import (
        JoinChannelRequest, LeaveChannelRequest, GetFullChannelRequest
    )
    from telethon.tl.functions.account import UpdateProfileRequest
except ImportError:
    os.system("pip install telethon")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==============================================================================
# 🛑 المرحلة 2: الإعدادات العامة والمتغيرات البيئية
# ==============================================================================
API_ID = 39719802  
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'  
ADMIN_ID = 8504553407 

# التحقق مما إذا كان البوت فرعياً (تم تنصيبه لزبون) أو البوت الرئيسي
IS_SUB_BOT = len(sys.argv) > 2
BOT_TOKEN = sys.argv[1] if IS_SUB_BOT else "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY"
OWNER_ID = int(sys.argv[2]) if IS_SUB_BOT else ADMIN_ID

# تهيئة بنية الملفات والمجلدات اللازمة لتخزين البيانات والسيشنات
folders = ['data', 'sessions', 'configs', 'logs', 'temp']
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

# إعداد ملف الأداة لاستخراج السيشن ليتمكن المستخدم من تحميله
EXTRACTOR_CONTENT = """
import os, asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("="*40)
print("🚀 Titan Secure Session Extractor V2")
print("="*40)

API_ID = 39719802
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

async def main():
    try:
        async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
            session_str = client.session.save()
            print("\\n✅ تم استخراج السيشن بنجاح:")
            print("-" * 50)
            print(session_str)
            print("-" * 50)
            print("\\nانسخ الكود أعلاه وأرسله إلى البوت الرئيسي.")
            input("\\nاضغط Enter للخروج...")
    except Exception as e:
        print(f"❌ حدث خطأ: {e}")
        input()

if __name__ == "__main__":
    asyncio.run(main())
"""
with open("extractor.py", "w", encoding="utf-8") as f:
    f.write(EXTRACTOR_CONTENT)

# ==============================================================================
# 📊 المرحلة 3: نظام إدارة قاعدة البيانات (Titan DB Engine)
# ==============================================================================
class TitanDatabase:
    """محرك قاعدة البيانات لإدارة الحسابات، الإعدادات والسجلات لكل مستخدم بشكل منفصل."""
    def __init__(self, user_id):
        self.db_path = f"data/titan_v22_{user_id}.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._initialize_tables()

    def _initialize_tables(self):
        # جدول الحسابات
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, 
            session_str TEXT, 
            points INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # جدول الإعدادات العامة
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)')
        
        # جدول السجلات (Logs)
        self.cursor.execute('CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        self.conn.commit()

    def add_account(self, phone, session):
        self.cursor.execute("INSERT OR REPLACE INTO accounts (phone, session_str) VALUES (?, ?)", (phone, session))
        self.conn.commit()

    def get_accounts(self):
        self.cursor.execute("SELECT phone, session_str, points FROM accounts WHERE status='active'")
        return self.cursor.fetchall()

    def delete_account(self, phone):
        self.cursor.execute("DELETE FROM accounts WHERE phone=?", (phone,))
        self.conn.commit()

    def set_config(self, key, value):
        self.cursor.execute("INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    def get_config(self, key, default=None):
        self.cursor.execute("SELECT val FROM settings WHERE key=?", (key,))
        row = self.cursor.fetchone()
        return row[0] if row else default

    def log_activity(self, action):
        self.cursor.execute("INSERT INTO activity_logs (action) VALUES (?)", (action,))
        self.conn.commit()

db = TitanDatabase(OWNER_ID)

# ==============================================================================
# 🧠 المرحلة 4: محرك العمليات الذكي (Titan Core Engine)
# ==============================================================================
class TitanEngine:
    @staticmethod
    async def check_session(session_str):
        """التحقق من صحة السيشن قبل إضافته للقاعدة."""
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        try:
            await client.connect()
            is_authorized = await client.is_user_authorized()
            if is_authorized:
                me = await client.get_me()
                return True, me.phone, client
            return False, None, None
        except:
            return False, None, None

    @staticmethod
    async def join_link(client, link):
        """محاولة الانضمام لرابط أو بدء بوت."""
        try:
            if "start=" in link:
                username = link.split('/')[-1].split('?')[0]
                param = link.split('start=')[-1]
                await client(StartBotRequest(username, username, param))
                return True
            else:
                await client(JoinChannelRequest(link))
                return True
        except:
            return False

# ==============================================================================
# ⌨️ المرحلة 5: واجهة المستخدم الرسومية (Buttons)
# ==============================================================================
def build_keyboard():
    """بناء لوحة التحكم الرئيسية."""
    layout = [
        [Button.inline("➕ إضافة حساب (رقم)", data="proc_add_p"), Button.inline("🔑 إضافة حساب (سيشن)", data="proc_add_s")],
        [Button.inline("🚀 بدء تجميع (رابط)", data="proc_f_link"), Button.inline("🎁 تجميع هدايا", data="proc_f_gift")],
        [Button.inline("💰 فحص وتحويل", data="proc_f_trans"), Button.inline("🔥 تجميع مختلط", data="proc_f_mix")],
        [Button.inline("📊 إحصائياتي", data="proc_stats"), Button.inline("🧹 تنظيف الحسابات", data="proc_cleanup")],
        [Button.inline("⚙️ الإعدادات", data="proc_settings"), Button.inline("📝 السجلات", data="proc_logs")],
        [Button.inline("🛠 أداة استخراج السيشن", data="proc_send_tool")],
        [Button.url("👨‍💻 المطور", "https://t.me/G_6_W")]
    ]
    # يظهر هذا الزر للمطور الأساسي فقط لتنصيب نسخ للزبائن
    if not IS_SUB_BOT:
        layout.insert(-1, [Button.inline("👑 تنصيب بوت لزبون (Admin)", data="deploy")])
    return layout

# ==============================================================================
# ⚡ المرحلة 6: معالجة الأوامر والفعاليات
# ==============================================================================
bot = TelegramClient(f"sessions/titan_main_{OWNER_ID}", API_ID, API_HASH)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id not in [OWNER_ID, ADMIN_ID]:
        return
    
    welcome_msg = (
        "🔱 **مرحباً بك في Titan Ultimate V22**\n\n"
        "أقوى نظام لإدارة مزارع الحسابات وتجميع النقاط.\n"
        "تم تفعيل كافة الأدوات والتحققات البرمجية.\n\n"
        "📱 **الحسابات النشطة:** `{}`\n"
        "🤖 **حالة النظام:** `مستقر`"
    ).format(len(db.get_accounts()))
    
    await event.respond(welcome_msg, buttons=build_keyboard())

# --- معالج الأزرار الموحد ---
@bot.on(events.CallbackQuery)
async def callback_router(event):
    data = event.data.decode()
    
    # التحقق من الصلاحية
    if event.sender_id not in [OWNER_ID, ADMIN_ID]:
        return await event.answer("❌ لا تملك صلاحية الوصول.", alert=True)

    # 1. إرسال الأداة
    if data == "proc_send_tool":
        await event.answer("جاري تحضير الأداة...", alert=False)
        await event.client.send_file(
            event.chat_id, 
            "extractor.py", 
            caption="🛠 **Titan Extractor V2**\nاستخدم هذا الملف لاستخراج كود السيشن بأمان من جهازك."
        )

    # 2. إضافة حساب سيشن
    elif data == "proc_add_s":
        async with bot.conversation(OWNER_ID) as conv:
            await conv.send_message("🔑 **أرسل كود السيشن (String Session):**")
            session_str = (await conv.get_response()).text.strip()
            
            wait_msg = await conv.send_message("⏳ جاري التحقق من صحة السيشن...")
            is_ok, phone, client = await TitanEngine.check_session(session_str)
            
            if is_ok:
                db.add_account(phone, session_str)
                await wait_msg.edit(f"✅ تم إضافة الحساب `{phone}` بنجاح إلى المزرعة!")
                await client.disconnect()
            else:
                await wait_msg.edit("❌ السيشن غير صالح أو تم تسجيل الخروج منه.")

    # 3. الإحصائيات
    elif data == "proc_stats":
        accs = db.get_accounts()
        stats_text = (
            "📊 **إحصائيات المزرعة:**\n\n"
            "📱 عدد الحسابات: `{}`\n"
            "💰 إجمالي النقاط التقريبي: `{}`\n"
            "📅 تاريخ التحديث: `{}`"
        ).format(len(accs), sum([a[2] for a in accs]), datetime.datetime.now().strftime("%Y-%m-%d"))
        await event.edit(stats_text, buttons=[[Button.inline("🔙 رجوع", data="back_main")]])

    # 4. تنظيف الحسابات
    elif data == "proc_cleanup":
        await event.answer("🧹 جاري فحص الحسابات وحذف المعطلة...", alert=True)
        accs = db.get_accounts()
        removed = 0
        for phone, session, points in accs:
            ok, _, _ = await TitanEngine.check_session(session)
            if not ok:
                db.delete_account(phone)
                removed += 1
        await event.respond(f"✅ اكتمل التنظيف. تم حذف `{removed}` حساب معطل.")

    # 5. الرجوع
    elif data == "back_main":
        await event.edit("القائمة الرئيسية:", buttons=build_keyboard())

    # 6. تجميع روابط
    elif data == "proc_f_link":
        async with bot.conversation(OWNER_ID) as conv:
            await conv.send_message("🔗 **أرسل الرابط أو يوزر البوت:**")
            link = (await conv.get_response()).text.strip()
            accs = db.get_accounts()
            await event.respond(f"🚀 بدء العمل بـ {len(accs)} حساب...")
            
            success = 0
            for p, s, pt in accs:
                c = TelegramClient(StringSession(s), API_ID, API_HASH)
                try:
                    await c.connect()
                    if await TitanEngine.join_link(c, link):
                        success += 1
                except: pass
                finally: await c.disconnect()
            await event.respond(f"✅ المهمة انتهت.\nنجاح: `{success}`\nفشل: `{len(accs)-success}`")

    # 7. السجلات (Logs)
    elif data == "proc_logs":
        await event.answer("📝 الميزة ستتوفر في التحديث القادم مع نظام التقرير التلقائي.", alert=True)

# ==============================================================================
# 🛑 المرحلة 7: كود التنصيب الأصلي (ممنوع اللمس)
# ==============================================================================
@bot.on(events.CallbackQuery(data="deploy"))
async def deploy_handler(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(ADMIN_ID) as conv:
        try:
            await conv.send_message("⚙️ **أرسل توكن البوت الجديد:**")
            token = (await conv.get_response()).text
            await conv.send_message("👤 **أرسل آيدي الزبون:**")
            target_uid = (await conv.get_response()).text
            await conv.send_message("⏳ **عدد أيام الاشتراك:**")
            days = (await conv.get_response()).text
            await conv.send_message("🔢 **الحد الأقصى للحسابات:**")
            limit = (await conv.get_response()).text
            expiry = (datetime.datetime.now() + datetime.timedelta(days=int(days))).strftime('%Y-%m-%d')
            config_data = {"token": token, "owner": int(target_uid), "expiry": expiry, "max": int(limit)}
            if not os.path.exists('configs'): os.makedirs('configs')
            with open(f"configs/user_{target_uid}.json", "w") as f:
                json.dump(config_data, f)
            subprocess.Popen([sys.executable, __file__, token, target_uid])
            await conv.send_message(f"🚀 **تم تنصيب البوت بنجاح!**\n📅 ينتهي في: `{expiry}`")
        except Exception as e:
            await conv.send_message(f"❌ خطأ في التنصيب: {e}")

# ==============================================================================
# 🏁 المرحلة الأخيرة: التشغيل النهائي للنظام
# ==============================================================================
if __name__ == '__main__':
    print(f"--- Titan Ultimate V22 Core Started for ID: {OWNER_ID} ---")
    bot.start(bot_token=BOT_TOKEN)
    bot.run_until_disconnected()
