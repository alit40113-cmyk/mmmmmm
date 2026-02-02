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

# ==========================================
# 🛑 المرحلة 1: الاعتمادات والتحقق
# ==========================================
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        StartBotRequest, GetHistoryRequest, GetBotCallbackAnswerRequest, SendMessageRequest
    )
    from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
except ImportError:
    os.system("pip install telethon")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==========================================
# 🛑 المرحلة 2: الإعدادات (API & IDs)
# ==========================================
API_ID = 39719802  
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'  
ADMIN_ID = 8504553407 

IS_SUB_BOT = len(sys.argv) > 2
BOT_TOKEN = sys.argv[1] if IS_SUB_BOT else "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY"
OWNER_ID = int(sys.argv[2]) if IS_SUB_BOT else ADMIN_ID

# تهيئة المجلدات
for folder in ['data', 'sessions', 'configs', 'logs']:
    if not os.path.exists(folder): os.makedirs(folder)

# ==========================================
# 📊 المرحلة 3: محرك قاعدة البيانات (Database)
# ==========================================
class TitanDatabase:
    def __init__(self, user_id):
        self.db_path = f"data/titan_v25_{user_id}.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._setup()

    def _setup(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, session_str TEXT, points INTEGER DEFAULT 0)''')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS activity_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, date TEXT)')
        self.conn.commit()

    def add_acc(self, phone, session):
        self.cursor.execute("INSERT OR REPLACE INTO accounts (phone, session_str) VALUES (?, ?)", (phone, session))
        self.conn.commit()

    def get_accs(self):
        self.cursor.execute("SELECT phone, session_str, points FROM accounts")
        return self.cursor.fetchall()

    def remove_acc(self, phone):
        self.cursor.execute("DELETE FROM accounts WHERE phone=?", (phone,))
        self.conn.commit()

    def set_val(self, key, val):
        self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(val)))
        self.conn.commit()

    def get_val(self, key, default=None):
        self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        res = self.cursor.fetchone()
        return res[0] if res else default

    def add_log(self, action):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cursor.execute("INSERT INTO activity_logs (action, date) VALUES (?, ?)", (action, now))
        self.conn.commit()

db = TitanDatabase(OWNER_ID)

# ==========================================
# 🧠 المرحلة 4: محرك العمليات (Worker Engine)
# ==========================================
class TitanWorker:
    def __init__(self, session):
        self.client = TelegramClient(StringSession(session), API_ID, API_HASH)

    async def run_task(self, task_type, data):
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized(): return False
            
            if task_type == "link":
                if "start=" in data:
                    bot_u = data.split('/')[-1].split('?')[0]
                    param = data.split('start=')[-1]
                    await self.client(StartBotRequest(bot_u, bot_u, param))
                else:
                    await self.client(JoinChannelRequest(data))
            
            elif task_type == "gift":
                # منطق تجميع الهدية
                bot_u = data.split('/')[-1].split('?')[0]
                param = data.split('start=')[-1]
                await self.client(StartBotRequest(bot_u, bot_u, param))

            elif task_type == "check":
                await self.client.send_message(data, "حسابي")
                await asyncio.sleep(2)
                msgs = await self.client.get_messages(data, limit=1)
                pts = re.findall(r'(\d+)', msgs[0].text.replace(',', ''))
                return int(pts[0]) if pts else 0

            return True
        except: return False
        finally: await self.client.disconnect()

# ==========================================
# ⌨️ المرحلة 5: معالجة الواجهة (UI & Events)
# ==========================================
app = TelegramClient(f"sessions/bot_main_{OWNER_ID}", API_ID, API_HASH)

def main_menu():
    return [
        [Button.inline("➕ إضافة حساب (رقم)", data="add_p"), Button.inline("🔑 إضافة حساب (سيشن)", data="add_s")],
        [Button.inline("🚀 بدء تجميع (رابط)", data="f_link"), Button.inline("🎁 تجميع هدايا", data="f_gift")],
        [Button.inline("💰 فحص وتحويل", data="f_trans"), Button.inline("🔥 تجميع مختلط", data="f_mix")],
        [Button.inline("📊 إحصائياتي", data="stats"), Button.inline("🧹 تنظيف الحسابات", data="cleanup")],
        [Button.inline("⚙️ الإعدادات", data="settings"), Button.inline("📝 السجلات", data="logs")],
        [Button.inline("🛠 أداة استخراج السيشن", data="send_tool")],
        [Button.url("👨‍💻 المطور", "https://t.me/G_6_W")],
        [Button.inline("🛠 تنصيب بوت لزبون (مطور)", data="deploy")] if not IS_SUB_BOT else []
    ]

@app.on(events.NewMessage(pattern='/start'))
async def start(e):
    if e.sender_id in [OWNER_ID, ADMIN_ID]:
        await e.respond("🔱 **Titan Ultimate V25 Active**\nالنظام جاهز للعمل بكافة الأزرار.", buttons=main_menu())

@app.on(events.CallbackQuery)
async def manager(event):
    data = event.data.decode()
    user = event.sender_id
    if user not in [OWNER_ID, ADMIN_ID]: return

    # --- زر تجميع الروابط ---
    if data == "f_link":
        async with app.conversation(user) as conv:
            await conv.send_message("🔗 أرسل الرابط (قناة أو رابط دعوة بوت):")
            link = (await conv.get_response()).text
            accs = db.get_accs()
            await event.respond(f"⏳ بدء العمل بـ {len(accs)} حساب...")
            for p, s, pt in accs:
                worker = TitanWorker(s)
                await worker.run_task("link", link)
                await asyncio.sleep(1)
            await event.respond("✅ اكتمل الانضمام لجميع الحسابات.")
            db.add_log(f"تجميع رابط: {link}")

    # --- زر تجميع الهدايا ---
    elif data == "f_gift":
        async with app.conversation(user) as conv:
            await conv.send_message("🎁 أرسل رابط الهدية:")
            link = (await conv.get_response()).text
            accs = db.get_accs()
            await event.respond("🎁 جاري سحب الهدايا...")
            for p, s, pt in accs:
                worker = TitanWorker(s)
                await worker.run_task("gift", link)
            await event.respond("✅ تم الانتهاء من محاولة سحب الهدايا.")

    # --- زر فحص وتحويل ---
    elif data == "f_trans":
        target = db.get_val("target_bot", "@Z88Bot")
        accs = db.get_accs()
        await event.respond(f"💰 جاري فحص الرصيد في {target}...")
        for p, s, pt in accs:
            worker = TitanWorker(s)
            pts = await worker.run_task("check", target)
            if pts: db.cursor.execute("UPDATE accounts SET points=? WHERE phone=?", (pts, p))
        db.conn.commit()
        await event.respond("✅ تم تحديث كافة الأرصدة في القاعدة.")

    # --- زر الإعدادات ---
    elif data == "settings":
        await event.edit("⚙️ **الإعدادات:**", buttons=[
            [Button.inline("تغيير البوت المستهدف", data="set_target")],
            [Button.inline("🔙 رجوع", data="main")]
        ])

    elif data == "set_target":
        async with app.conversation(user) as conv:
            await conv.send_message("🤖 أرسل يوزر البوت (مثال: @Z88Bot):")
            u = (await conv.get_response()).text
            db.set_val("target_bot", u)
            await conv.send_message(f"✅ تم الحفظ: {u}")

    # --- زر السجلات ---
    elif data == "logs":
        db.cursor.execute("SELECT action, date FROM activity_logs ORDER BY id DESC LIMIT 10")
        res = db.cursor.fetchall()
        txt = "📝 **السجلات:**\n\n" + "\n".join([f"• {r[0]} | {r[1]}" for r in res])
        await event.edit(txt, buttons=[[Button.inline("🔙 رجوع", data="main")]])

    # --- زر إضافة سيشن ---
    elif data == "add_s":
        async with app.conversation(user) as conv:
            await conv.send_message("🔑 أرسل كود السيشن:")
            s = (await conv.get_response()).text.strip()
            # فحص السيشن
            c = TelegramClient(StringSession(s), API_ID, API_HASH)
            try:
                await c.connect()
                me = await c.get_me()
                db.add_acc(me.phone, s)
                await conv.send_message(f"✅ تم إضافة: {me.phone}")
            except: await conv.send_message("❌ سيشن خاطئ.")
            finally: await c.disconnect()

    # --- زر الرجوع ---
    elif data == "main":
        await event.edit("القائمة الرئيسية:", buttons=main_menu())

# ==========================================
# 🛑 كود التنصيب (لا تلمسه - كما هو تماماً)
# ==========================================
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
# 🏁 التشغيل
# ==========================================
if __name__ == '__main__':
    app.start(bot_token=BOT_TOKEN)
    app.run_until_disconnected()
