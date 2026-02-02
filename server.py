import asyncio
import os
import sys
import json
import datetime
import sqlite3
import subprocess
import re
import time
import random
from typing import List, Dict, Any, Optional

# ==========================================
# 🛑 تثبيت وتأمين المكتبات
# ==========================================
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        StartBotRequest, GetHistoryRequest, ReadHistoryRequest
    )
    from telethon.tl.functions.channels import (
        JoinChannelRequest, LeaveChannelRequest, GetFullChannelRequest
    )
except ImportError:
    print("📦 جاري تثبيت المكتبات الأساسية لضمان عمل المزرعة...")
    os.system("pip install telethon")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==========================================
# 🛑 الإعدادات البرمجية الصارمة
# ==========================================
API_ID = 39719802  
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'  
ADMIN_ID = 8504553407 

# نظام التعرف على النسخة (أصلية أم فرعية)
IS_SUB_BOT = len(sys.argv) > 2
BOT_TOKEN = sys.argv[1] if IS_SUB_BOT else "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY"
OWNER_ID = int(sys.argv[2]) if IS_SUB_BOT else ADMIN_ID

# تهيئة بيئة العمل
DIRS = ['data', 'sessions', 'configs', 'logs']
for d in DIRS:
    if not os.path.exists(d): os.makedirs(d)

# إنشاء أداة الاستخراج تلقائياً
EXTRACTOR_PATH = "extractor.py"
with open(EXTRACTOR_PATH, "w", encoding="utf-8") as f:
    f.write("""
import os, asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("🚀 أداة تيتان لاستخراج السيشن")
API_ID = 39719802
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\\n✅ مبروك! هذا هو السيشن الخاص بك:\\n")
        print(client.session.save())
        print("\\nنسخه وأرسله للبوت الرئيسي.")
        input("\\nاضغط Enter للخروج...")

if __name__ == "__main__":
    asyncio.run(main())
""")

# ==========================================
# 📊 محرك قاعدة البيانات (Enterprise Layer)
# ==========================================
class TitanDB:
    def __init__(self, uid):
        self.conn = sqlite3.connect(f"data/titan_v15_{uid}.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._setup()

    def _setup(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, session TEXT, points INTEGER DEFAULT 0, 
            added_date TEXT, status TEXT DEFAULT 'active')''')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)')
        self.conn.commit()

    def add_account(self, phone, session):
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cursor.execute("INSERT OR REPLACE INTO accounts (phone, session, added_date) VALUES (?, ?, ?)", 
                           (phone, session, date))
        self.conn.commit()

    def get_accounts(self):
        self.cursor.execute("SELECT phone, session, points FROM accounts WHERE status='active'")
        return self.cursor.fetchall()

    def delete_account(self, phone):
        self.cursor.execute("DELETE FROM accounts WHERE phone=?", (phone,))
        self.conn.commit()

db = TitanDB(OWNER_ID)

# ==========================================
# 🧠 محرك الفحص والتحقق الذكي
# ==========================================
class Validator:
    @staticmethod
    async def check_session(session_str):
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        try:
            await client.connect()
            is_ok = await client.is_user_authorized()
            return is_ok, client
        except: return False, None

# ==========================================
# 🖥️ واجهة المستخدم (UI Engine)
# ==========================================
def get_buttons():
    layout = [
        [Button.inline("➕ إضافة حساب (رقم)", data="add_p"), Button.inline("🔑 إضافة حساب (سيشن)", data="add_s")],
        [Button.inline("🚀 بدء تجميع (رابط)", data="f_link"), Button.inline("🎁 تجميع هدايا", data="f_gift")],
        [Button.inline("🛠 أداة استخراج السيشن", data="send_tool")],
        [Button.inline("💰 فحص وتحويل", data="f_trans"), Button.inline("🔥 تجميع مختلط", data="f_mix")],
        [Button.inline("📊 إحصائياتي", data="stats"), Button.inline("🧹 تنظيف الحسابات", data="cleanup")],
        [Button.inline("⚙️ الإعدادات", data="settings"), Button.inline("📝 السجلات", data="logs")],
        [Button.url("👨‍💻 المطور", "https://t.me/G_6_W")] # زر المطور
    ]
    if not IS_SUB_BOT:
        layout.insert(-1, [Button.inline("👑 تنصيب بوت لزبون (Admin)", data="deploy")])
    return layout

# ==========================================
# ⚡ النواة البرمجية (The Master Core)
# ==========================================
client = TelegramClient(f"sessions/master_{OWNER_ID}", API_ID, API_HASH)

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id not in [OWNER_ID, ADMIN_ID]: return
    welcome_msg = (
        "🔱 **أهلاً بك في نظام Titan Ultimate V15**\n\n"
        "هذا البوت هو محركك الخاص لإدارة مزارع الحسابات وتجميع النقاط.\n"
        "استخدم الأزرار أدناه للتحكم الكامل."
    )
    await event.respond(welcome_msg, buttons=get_buttons())

# --- [ وظيفة إرسال الأداة مع نص تعليمي ] ---
@client.on(events.CallbackQuery(data="send_tool"))
async def send_tool(event):
    await event.answer("جاري تحضير "الملف السحري"...", alert=False)
    instruction = (
        "🛠 **أداة استخراج السيشن (Titan Extractor)**\n\n"
        "1️⃣ قم بتحميل الملف المرفق على حاسوبك.\n"
        "2️⃣ تأكد من تثبيت مكتبة Telethon (`pip install telethon`).\n"
        "3️⃣ شغل الملف، ادخل رقمك وكود التحقق.\n"
        "4️⃣ سيظهر لك كود طويل (السيشن)، انسخه وأرسله للبوت هنا.\n\n"
        "⚠️ **ملاحظة:** السيشن هو مفتاح دخولك، لا تعطه لأحد أبداً!"
    )
    await event.client.send_file(event.chat_id, EXTRACTOR_PATH, caption=instruction)

# --- [ إضافة السيشن مع التحقق الفوري ] ---
@client.on(events.CallbackQuery(data="add_s"))
async def add_session_verified(event):
    async with client.conversation(OWNER_ID) as conv:
        await conv.send_message("📱 **أرسل رقم الهاتف المرتبط بالسيشن:**")
        phone = (await conv.get_response()).text.strip()
        
        await conv.send_message("🔑 **الآن أرسل كود السيشن (String Session):**")
        session_str = (await conv.get_response()).text.strip()
        
        await conv.send_message("⏳ **جاري التحقق من الحساب برمجياً...**")
        is_valid, test_c = await Validator.check_session(session_str)
        
        if is_valid:
            db.add_account(phone, session_str)
            await conv.send_message(f"✅ **تم التحقق!** الحساب `{phone}` نشط ومضاف للمزرعة.")
            await test_c.disconnect()
        else:
            await conv.send_message("❌ **فشل التحقق!** السيشن غير صالح أو الحساب محظور.")

# --- [ بدء التجميع بالرابط مع التحقق من النتائج ] ---
@client.on(events.CallbackQuery(data="f_link"))
async def farm_link(event):
    async with client.conversation(OWNER_ID) as conv:
        await conv.send_message("🔗 **أرسل رابط الدعوة أو يوزر البوت:**")
        link = (await conv.get_response()).text.strip()
        accounts = db.get_accounts()
        
        await event.respond(f"🚀 **بدأ الهجوم!** جاري التجميع بـ {len(accounts)} حساب...")
        
        success, fail = 0, 0
        for p, s, pt in accounts:
            is_ok, worker = await Validator.check_session(s)
            if is_ok:
                try:
                    if "start=" in link:
                        bot_username = link.split('/')[-1].split('?')[0]
                        param = link.split('start=')[-1]
                        await worker(StartBotRequest(bot_username, bot_username, param))
                    else:
                        await worker(JoinChannelRequest(link))
                    success += 1
                except: fail += 1
                finally: await worker.disconnect()
            else: fail += 1
            
        await event.respond(f"📊 **تقرير العملية:**\n✅ نجاح: `{success}`\n❌ فشل/حظر: `{fail}`")

# --- [ تنظيف المزرعة (Cleanup) ] ---
@client.on(events.CallbackQuery(data="cleanup"))
async def cleanup_farm(event):
    await event.answer("🧹 جاري تصفية الحسابات الميتة...", alert=True)
    accounts = db.get_accounts()
    dead = 0
    for p, s, pt in accounts:
        is_ok, _ = await Validator.check_session(s)
        if not is_ok:
            db.delete_account(p)
            dead += 1
    await event.respond(f"✅ **اكتمل التنظيف!**\nتم حذف `{dead}` حساب معطل.")

# --- [ إحصائيات المزرعة ] ---
@client.on(events.CallbackQuery(data="stats"))
async def show_stats(event):
    accs = db.get_accounts()
    msg = (
        f"📊 **إحصائيات المزرعة الملكية:**\n\n"
        f"📱 إجمالي الحسابات: `{len(accs)}`\n"
        f"💰 النقاط المخزنة: `{sum(a[2] for a in accs)}`"
    )
    await event.edit(msg, buttons=[[Button.inline("🔙 رجوع", data="main")]])

# --- [ العودة للقائمة ] ---
@client.on(events.CallbackQuery(data="main"))
async def back_home(event):
    await event.edit("القائمة الرئيسية:", buttons=get_buttons())

# --- [ نظام التنصيب (Admin Only) ] ---
@client.on(events.CallbackQuery(data="deploy"))
async def deploy_system(event):
    if event.sender_id != ADMIN_ID: return
    async with client.conversation(ADMIN_ID) as conv:
        try:
            await conv.send_message("⚙️ **توكن بوت الزبون:**")
            t = (await conv.get_response()).text
            await conv.send_message("👤 **آيدي الزبون:**")
            u = (await conv.get_response()).text
            await conv.send_message("⏳ **عدد الأيام:**")
            d = (await conv.get_response()).text
            exp = (datetime.datetime.now() + datetime.timedelta(days=int(d))).strftime('%Y-%m-%d')
            
            subprocess.Popen([sys.executable, __file__, t, u])
            await conv.send_message(f"🚀 **تم إطلاق البوت بنجاح!**\nالزبون: `{u}`\nينتهي: `{exp}`")
        except Exception as e: await conv.send_message(f"❌ خطأ: {e}")

# ==========================================
# 🏁 إطلاق المحرك
# ==========================================
if __name__ == '__main__':
    print(f"🔱 Titan Core V15 Is Active for ID: {OWNER_ID}")
    client.start(bot_token=BOT_TOKEN)
    client.run_until_disconnected()
