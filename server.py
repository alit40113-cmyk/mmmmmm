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

# 

# ==========================================
# 🛑 تثبيت المكتبات اللازمة تلقائياً
# ==========================================
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        StartBotRequest, 
        ReadHistoryRequest, 
        GetHistoryRequest, 
        GetBotCallbackAnswerRequest
    )
    from telethon.tl.functions.channels import (
        JoinChannelRequest, 
        LeaveChannelRequest, 
        GetFullChannelRequest
    )
except ImportError:
    print("📦 جاري تثبيت المكتبات المفقودة...")
    os.system("pip install telethon")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==========================================
# 🛑 الإعدادات الأساسية (Global Config)
# ==========================================
API_ID = 39719802  
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'  
ADMIN_ID = 8504553407 

IS_SUB_BOT = len(sys.argv) > 2
BOT_TOKEN = sys.argv[1] if IS_SUB_BOT else "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY"
OWNER_ID = int(sys.argv[2]) if IS_SUB_BOT else ADMIN_ID

# إعدادات المجلدات
DIRS = ['data', 'sessions', 'configs', 'logs']
for d in DIRS:
    if not os.path.exists(d):
        os.makedirs(d)

# ==========================================
# 📊 نظام قاعدة البيانات الشامل (Enterprise DB)
# ==========================================
class DatabaseManager:
    def __init__(self, user_id):
        self.db_path = f"data/database_{user_id}.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, session_str TEXT NOT NULL, points_total INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active', added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_collect TIMESTAMP)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, details TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.commit()

    def get_setting(self, key, default=None):
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        res = self.cursor.fetchone()
        return res[0] if res else default

    def set_setting(self, key, value):
        self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    def add_acc(self, phone, session):
        self.cursor.execute("INSERT OR REPLACE INTO accounts (phone, session_str) VALUES (?, ?)", (phone, session))
        self.conn.commit()

    def get_all_accounts(self):
        self.cursor.execute("SELECT phone, session_str FROM accounts WHERE status = 'active'")
        return self.cursor.fetchall()

    def log_event(self, action, details):
        self.cursor.execute("INSERT INTO logs (action, details) VALUES (?, ?)", (action, details))
        self.conn.commit()

db = DatabaseManager(OWNER_ID)

# ==========================================
# 🧠 محرك التجميع (Collection Engine)
# ==========================================
class TitanEngine:
    @staticmethod
    def extract_points(text: str) -> int:
        try:
            numbers = re.findall(r'(\d+)', text.replace(',', ''))
            return int(numbers[0]) if numbers else 0
        except: return 0

# ==========================================
# 🛠️ مدير المهام (Worker Manager)
# ==========================================
class FarmWorker:
    def __init__(self, phone, session_str):
        self.phone = phone
        self.session = session_str
        self.client = None

    async def start_client(self):
        try:
            self.client = TelegramClient(StringSession(self.session), API_ID, API_HASH)
            await self.client.connect()
            return await self.client.is_user_authorized()
        except: return False

    async def collect_gift(self, bot_username):
        if not await self.start_client(): return "offline"
        try:
            await self.client.send_message(bot_username, "/start")
            await asyncio.sleep(2)
            history = await self.client(GetHistoryRequest(peer=bot_username, offset_id=0, offset_date=None, add_offset=0, limit=1, max_id=0, min_id=0, hash=0))
            if history.messages and history.messages[0].reply_markup:
                for row in history.messages[0].reply_markup.rows:
                    for btn in row.buttons:
                        if any(x in btn.text for x in ["هدية", "يومية", "Daily", "Gift"]):
                            await history.messages[0].click(button=btn)
                            return "success"
            return "no_button"
        except: return "error"
        finally: await self.client.disconnect()

# ==========================================
# ⌨️ واجهة المستخدم المتقدمة (UI Design)
# ==========================================
def get_main_menu():
    btns = [
        [Button.inline("➕ إضافة حساب (رقم)", data="add_p"), Button.inline("🔑 إضافة حساب (سيشن)", data="add_s")],
        [Button.inline("🚀 بدء تجميع (رابط)", data="f_link"), Button.inline("🎁 تجميع هدايا", data="f_gift")],
        [Button.inline("📊 إحصائياتي", data="stats"), Button.inline("📝 السجلات", data="logs")],
        [Button.inline("🧹 تنظيف الحسابات", data="cleanup"), Button.inline("⚙️ الإعدادات", data="settings")]
    ]
    if not IS_SUB_BOT:
        btns.append([Button.inline("🛠 تنصيب بوت لزبون (مطور)", data="deploy")])
    return btns

# ==========================================
# ⚡ النواة البرمجية للبوت (The Core)
# ==========================================
app = TelegramClient(f"sessions/owner_{OWNER_ID}", API_ID, API_HASH)

@app.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id != OWNER_ID and event.sender_id != ADMIN_ID: return
    await event.respond(f"🔱 **نظام Titan Ultimate V11**\n\n👤 المستخدم: `{OWNER_ID}`\n📈 الحالة: `مستقر ومصلح ✅`", buttons=get_main_menu())

# --- [ إصلاح إضافة السيشن ومنع الـ NoneType Error ] ---
@app.on(events.CallbackQuery(data="add_s"))
async def add_session_fix(event):
    async with app.conversation(OWNER_ID) as conv:
        try:
            p_msg = await conv.send_message("📞 **أرسل رقم الهاتف أولاً مع الرمز:**")
            resp_phone = await conv.get_response()
            if not resp_phone.text: return await conv.send_message("❌ خطأ: لم ترسل نصاً.")
            phone = resp_phone.text.strip()

            s_msg = await conv.send_message("🔑 **أرسل كود السيشن (String Session):**")
            resp_sess = await conv.get_response()
            if not resp_sess.text: return await conv.send_message("❌ خطأ: السيشن فارغ.")
            session = resp_sess.text.strip()

            # فحص السيشن قبل الحفظ
            await conv.send_message("⏳ جاري فحص السيشن...")
            test_client = TelegramClient(StringSession(session), API_ID, API_HASH)
            await test_client.connect()
            if await test_client.is_user_authorized():
                db.add_acc(phone, session)
                db.log_event("Add Session", f"Success: {phone}")
                await conv.send_message(f"✅ تم إضافة الحساب `{phone}` بنجاح!")
            else:
                await conv.send_message("❌ السيشن الذي أرسلته غير صالح أو منتهي.")
            await test_client.disconnect()
        except Exception as e:
            await conv.send_message(f"❌ حدث خطأ غير متوقع: {str(e)}")

# --- [ تفعيل أزرار التجميع ] ---
@app.on(events.CallbackQuery(data="f_gift"))
async def farm_gift_handler(event):
    accounts = db.get_all_accounts()
    if not accounts: return await event.answer("⚠️ لا توجد حسابات مضافة!", alert=True)
    
    await event.answer("🔄 بدأت عملية تجميع الهدايا لجميع الحسابات...", alert=False)
    target = db.get_setting("target_bot", "@Z88Bot")
    
    success = 0
    for phone, session in accounts:
        worker = FarmWorker(phone, session)
        res = await worker.collect_gift(target)
        if res == "success": success += 1
    
    await event.respond(f"🎁 **اكتمل تجميع الهدايا:**\n✅ نجاح: `{success}`\n❌ فشل: `{len(accounts)-success}`")

@app.on(events.CallbackQuery(data="stats"))
async def stats_callback(event):
    db.cursor.execute("SELECT count(*) FROM accounts")
    count = db.cursor.fetchone()[0]
    await event.edit(f"📊 **إحصائيات المزرعة:**\n\n📱 عدد الحسابات: `{count}`\n🤖 البوت المستهدف: `{db.get_setting('target_bot', '@Z88Bot')}`", buttons=[[Button.inline("🔙 رجوع", data="main")]])

@app.on(events.CallbackQuery(data="logs"))
async def show_logs(event):
    db.cursor.execute("SELECT action, created_at FROM logs ORDER BY id DESC LIMIT 10")
    logs = db.cursor.fetchall()
    log_text = "📝 **آخر العمليات:**\n\n" + "\n".join([f"- {a} | {d}" for a, d in logs])
    await event.edit(log_text, buttons=[[Button.inline("🔙 رجوع", data="main")]])

@app.on(events.CallbackQuery(data="main"))
async def back_to_main(event):
    await event.edit("القائمة الرئيسية:", buttons=get_main_menu())

# --- [ كود التنصيب - لم يتم لمسه بناءً على طلبك ] ---
@app.on(events.CallbackQuery(data="deploy"))
async def deploy_handler(event):
    if event.sender_id != ADMIN_ID: return
    async with app.conversation(ADMIN_ID) as conv:
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

# ==========================================
# 🏁 إطلاق النظام (Bootstrap)
# ==========================================
async def background_loop():
    while True: await asyncio.sleep(3600)

async def start_system():
    try:
        await app.start(bot_token=BOT_TOKEN)
        print(f"✅ Bot {OWNER_ID} Is Online")
        db.log_event("System Start", "Online")
        await app.run_until_disconnected()
    except Exception as e: print(f"❌ Error: {e}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(background_loop())
    loop.run_until_complete(start_system())
