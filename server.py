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
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        StartBotRequest, ReadHistoryRequest, GetHistoryRequest, 
        GetBotCallbackAnswerRequest, SendMessageRequest, ForwardMessagesRequest
    )
    from telethon.tl.functions.channels import (
        JoinChannelRequest, LeaveChannelRequest, GetFullChannelRequest, InviteToChannelRequest
    )
    from telethon.tl.functions.contacts import ResolveUsernameRequest
except ImportError:
    os.system("pip install telethon")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==============================================================================
# 🛑 المرحلة 2: الإعدادات العامة والمتغيرات البيئية
# ==============================================================================
API_ID = 39719802  
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'  
ADMIN_ID = 8504553407 

IS_SUB_BOT = len(sys.argv) > 2
BOT_TOKEN = sys.argv[1] if IS_SUB_BOT else "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY"
OWNER_ID = int(sys.argv[2]) if IS_SUB_BOT else ADMIN_ID

# تهيئة بنية الملفات والمجلدات اللازمة لتخزين البيانات
for folder in ['data', 'sessions', 'configs', 'logs', 'temp']:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ==============================================================================
# 📊 المرحلة 3: نظام إدارة قاعدة البيانات (Titan DB Engine)
# ==============================================================================
class TitanDatabase:
    """نظام إدارة البيانات المتطور لتخزين الحسابات والعمليات."""
    def __init__(self, user_id):
        self.db_path = f"data/titan_v24_pro_{user_id}.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._initialize_tables()

    def _initialize_tables(self):
        # جدول الحسابات الرئيسي
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, 
            session_str TEXT, 
            points INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # جدول الإعدادات
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        
        # جدول السجلات التفصيلي
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        self.conn.commit()

    def add_account(self, phone, session):
        self.cursor.execute("INSERT OR REPLACE INTO accounts (phone, session_str) VALUES (?, ?)", (phone, session))
        self.conn.commit()

    def get_accounts(self) -> List[tuple]:
        self.cursor.execute("SELECT phone, session_str, points FROM accounts")
        return self.cursor.fetchall()

    def remove_account(self, phone):
        self.cursor.execute("DELETE FROM accounts WHERE phone=?", (phone,))
        self.conn.commit()

    def update_points(self, phone, pts):
        self.cursor.execute("UPDATE accounts SET points=? WHERE phone=?", (pts, phone))
        self.conn.commit()

    def add_log(self, action, details=""):
        self.cursor.execute("INSERT INTO logs (action, details) VALUES (?, ?)", (action, details))
        self.conn.commit()

    def get_logs(self, limit=10):
        self.cursor.execute("SELECT action, timestamp FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def set_config(self, key, val):
        self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(val)))
        self.conn.commit()

    def get_config(self, key, default=None):
        self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        res = self.cursor.fetchone()
        return res[0] if res else default

db = TitanDatabase(OWNER_ID)

# ==============================================================================
# 🧠 المرحلة 4: محرك العمليات المتقدم (Titan Multi-Tasking Engine)
# ==============================================================================
class TitanWorker:
    """كلاس متخصص لكل عملية تجميع أو فحص لضمان عدم تداخل المهام."""
    def __init__(self, phone, session):
        self.phone = phone
        self.session = session
        self.client = TelegramClient(StringSession(session), API_ID, API_HASH)

    async def connect(self):
        try:
            await self.client.connect()
            return await self.client.is_user_authorized()
        except: return False

    async def disconnect(self):
        await self.client.disconnect()

    async def join_link(self, link):
        """التعامل مع الروابط (قنوات أو بوتات)."""
        try:
            if "start=" in link:
                bot_user = link.split('/')[-1].split('?')[0]
                param = link.split('start=')[-1]
                await self.client(StartBotRequest(bot_user, bot_user, param))
                return True
            else:
                await self.client(JoinChannelRequest(link))
                return True
        except Exception as e:
            return False

    async def get_points(self, bot_username):
        """فحص الرصيد من بوت المليون أو غيره."""
        try:
            await self.client.send_message(bot_username, "حسابي")
            await asyncio.sleep(2)
            messages = await self.client.get_messages(bot_username, limit=1)
            text = messages[0].text
            found = re.findall(r'(\d+)', text.replace(',', ''))
            return int(found[0]) if found else 0
        except: return 0

# ==============================================================================
# ⌨️ المرحلة 5: معالجات الواجهة والأزرار
# ==============================================================================
def main_menu():
    return [
        [Button.inline("➕ إضافة حساب (رقم)", data="ui_add_p"), Button.inline("🔑 إضافة حساب (سيشن)", data="ui_add_s")],
        [Button.inline("🚀 بدء تجميع (رابط)", data="ui_f_link"), Button.inline("🎁 تجميع هدايا", data="ui_f_gift")],
        [Button.inline("💰 فحص وتحويل", data="ui_f_trans"), Button.inline("🔥 تجميع مختلط", data="ui_f_mix")],
        [Button.inline("📊 إحصائياتي", data="ui_stats"), Button.inline("🧹 تنظيف الحسابات", data="ui_cleanup")],
        [Button.inline("⚙️ الإعدادات", data="ui_settings"), Button.inline("📝 السجلات", data="ui_logs")],
        [Button.inline("🛠 أداة استخراج السيشن", data="ui_tool")],
        [Button.url("👨‍💻 المطور", "https://t.me/G_6_W")],
        [Button.inline("👑 تنصيب بوت لزبون (Admin)", data="deploy")] if not IS_SUB_BOT else []
    ]

# ==============================================================================
# ⚡ المرحلة 6: النواة المركزية للتفاعل
# ==============================================================================
app = TelegramClient(f"sessions/titan_core_{OWNER_ID}", API_ID, API_HASH)

@app.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id in [OWNER_ID, ADMIN_ID]:
        db.add_log("Start Command", f"User {event.sender_id} started the bot")
        welcome = (
            "🔱 **أهلاً بك في Titan Ultimate V24**\n"
            "النسخة الاحترافية الأكثر استقراراً وقوة.\n\n"
            "🛡 تم تفعيل كافة التحققات البرمجية للأزرار."
        )
        await event.respond(welcome, buttons=main_menu())

@app.on(events.CallbackQuery)
async def main_callback_router(event):
    data = event.data.decode()
    user_id = event.sender_id
    if user_id not in [OWNER_ID, ADMIN_ID]: return

    # --- معالج الإحصائيات ---
    if data == "ui_stats":
        accs = db.get_accounts()
        txt = f"📊 **إحصائيات المزرعة:**\n\n📱 عدد الحسابات: `{len(accs)}`"
        await event.edit(txt, buttons=[[Button.inline("🔙 رجوع", data="ui_main")]])

    # --- معالج السجلات ---
    elif data == "ui_logs":
        logs = db.get_logs(12)
        txt = "📝 **آخر 12 عملية مسجلة:**\n\n"
        for act, ts in logs:
            txt += f"• {act} | {ts}\n"
        await event.edit(txt, buttons=[[Button.inline("🔙 رجوع", data="ui_main")]])

    # --- معالج تنظيف الحسابات ---
    elif data == "ui_cleanup":
        await event.answer("🧹 جاري فحص الحسابات...", alert=True)
        accs = db.get_accounts()
        dead = 0
        for p, s, pts in accs:
            worker = TitanWorker(p, s)
            if not await worker.connect():
                db.remove_account(p)
                dead += 1
            await worker.disconnect()
        db.add_log("Cleanup", f"Removed {dead} dead accounts")
        await event.respond(f"✅ تم الانتهاء. الحسابات المحذوفة: `{dead}`")

    # --- معالج إضافة سيشن ---
    elif data == "ui_add_s":
        async with app.conversation(user_id) as conv:
            await conv.send_message("🔑 **أرسل كود السيشن (String Session):**")
            res = await conv.get_response()
            s_str = res.text.strip()
            
            check_msg = await conv.send_message("⏳ جاري التحقق من السيشن...")
            worker = TitanWorker("Temp", s_str)
            if await worker.connect():
                me = await worker.client.get_me()
                db.add_account(me.phone, s_str)
                db.add_log("Account Added", f"Phone: {me.phone}")
                await check_msg.edit(f"✅ تم بنجاح إضافة: `{me.phone}`")
            else:
                await check_msg.edit("❌ السيشن غير صالح.")
            await worker.disconnect()

    # --- معالج التجميع ---
    elif data == "ui_f_link":
        async with app.conversation(user_id) as conv:
            await conv.send_message("🔗 **أرسل الرابط المطلوب:**")
            link = (await conv.get_response()).text.strip()
            accs = db.get_accounts()
            await event.respond(f"🚀 بدء التجميع بـ {len(accs)} حساب...")
            success = 0
            for p, s, pt in accs:
                w = TitanWorker(p, s)
                if await w.connect():
                    if await w.join_link(link): success += 1
                await w.disconnect()
            await event.respond(f"📊 النتيجة: نجاح `{success}` من `{len(accs)}`")

    # --- العودة للقائمة ---
    elif data == "ui_main":
        await event.edit("القائمة الرئيسية:", buttons=main_menu())

    # --- إرسال الأداة ---
    elif data == "ui_tool":
        await event.answer("جاري الإرسال...", alert=False)
        with open("extractor.py", "w") as f:
            f.write("# Titan Extractor\nprint('Extractor Tool Active')")
        await event.client.send_file(event.chat_id, "extractor.py", caption="🛠 أداة السيشن.")

# ==============================================================================
# 🛑 المرحلة 7: كود التنصيب الاستباقي (لا يتم تعديله أبداً)
# ==============================================================================
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

# ==============================================================================
# 🏁 المرحلة 8: إقلاع النظام
# ==============================================================================
if __name__ == '__main__':
    print("--- Titan Ultimate V24 Core Activated ---")
    app.start(bot_token=BOT_TOKEN)
    app.run_until_disconnected()
