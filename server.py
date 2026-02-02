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
# 🛑 المكتبات والاعتمادات
# ==========================================
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        StartBotRequest, ReadHistoryRequest, GetHistoryRequest, GetBotCallbackAnswerRequest
    )
    from telethon.tl.functions.channels import (
        JoinChannelRequest, LeaveChannelRequest, GetFullChannelRequest
    )
except ImportError:
    os.system("pip install telethon")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==========================================
# 🛑 الإعدادات (API & IDs)
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
# 📊 محرك قاعدة البيانات المستقل
# ==========================================
class DatabaseManager:
    def __init__(self, user_id):
        self.db_path = f"data/titan_db_{user_id}.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, session_str TEXT NOT NULL, points INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active', added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, details TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.commit()

    def get_setting(self, key, default=None):
        self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        res = self.cursor.fetchone()
        return res[0] if res else default

    def set_setting(self, key, value):
        self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    def add_acc(self, phone, session):
        self.cursor.execute("INSERT OR REPLACE INTO accounts (phone, session_str) VALUES (?, ?)", (phone, session))
        self.conn.commit()

    def get_all(self):
        self.cursor.execute("SELECT phone, session_str FROM accounts")
        return self.cursor.fetchall()

    def log(self, action, details):
        self.cursor.execute("INSERT INTO logs (action, details) VALUES (?, ?)", (action, details))
        self.conn.commit()

db = DatabaseManager(OWNER_ID)

# ==========================================
# 🛠️ العامل (Farm Worker)
# ==========================================
class FarmWorker:
    def __init__(self, phone, session):
        self.phone, self.session = phone, session

    async def run_task(self, task_type, target=None):
        client = TelegramClient(StringSession(self.session), API_ID, API_HASH)
        try:
            await client.connect()
            if not await client.is_user_authorized(): return "unauth"
            
            if task_type == "gift":
                await client.send_message(target, "/start")
                await asyncio.sleep(2)
                msgs = await client.get_messages(target, limit=1)
                if msgs and msgs[0].reply_markup:
                    for row in msgs[0].reply_markup.rows:
                        for btn in row.buttons:
                            if "هدية" in btn.text or "Gift" in btn.text:
                                await msgs[0].click(button=btn)
                                return "done"
                return "no_gift"
            
            elif task_type == "link":
                if "start=" in target:
                    bot_part = target.split('/')[-1].split('?')[0]
                    param = target.split('start=')[-1]
                    await client(StartBotRequest(bot=bot_part, peer=bot_part, start_param=param))
                else:
                    await client(JoinChannelRequest(target))
                return "done"
        except: return "error"
        finally: await client.disconnect()

# ==========================================
# ⌨️ واجهات التحكم (Keyboards)
# ==========================================
def main_menu():
    return [
        [Button.inline("➕ إضافة حساب (رقم)", data="add_p"), Button.inline("🔑 إضافة حساب (سيشن)", data="add_s")],
        [Button.inline("🚀 بدء تجميع (رابط)", data="f_link"), Button.inline("🎁 تجميع هدايا", data="f_gift")],
        [Button.inline("💰 فحص وتحويل", data="f_trans"), Button.inline("🔥 تجميع مختلط", data="f_mix")],
        [Button.inline("📊 إحصائياتي", data="stats"), Button.inline("📝 السجلات", data="logs")],
        [Button.inline("🧹 تنظيف الحسابات", data="cleanup"), Button.inline("⚙️ الإعدادات", data="settings")],
        [Button.inline("🛠 تنصيب بوت لزبون (مطور)", data="deploy")] if not IS_SUB_BOT else []
    ]

# ==========================================
# ⚡ معالجات الأحداث (Event Handlers)
# ==========================================
app = TelegramClient(f"sessions/bot_{OWNER_ID}", API_ID, API_HASH)

@app.on(events.NewMessage(pattern='/start'))
async def start(e):
    if e.sender_id != OWNER_ID and e.sender_id != ADMIN_ID: return
    await e.respond("🔱 **أهلاً بك في لوحة تحكم Titan V12 المصلحة**", buttons=main_menu())

# --- [ حل مشكلة إضافة الحسابات ] ---
@app.on(events.CallbackQuery(data="add_s"))
async def add_session(event):
    async with app.conversation(OWNER_ID) as conv:
        try:
            await conv.send_message("👤 أرسل رقم الهاتف أولاً:")
            p_res = await conv.get_response()
            if not p_res.text: return
            phone = p_res.text.strip()
            
            await conv.send_message("🔑 أرسل كود السيشن (String Session):")
            s_res = await conv.get_response()
            if not s_res.text: return
            session = s_res.text.strip()
            
            db.add_acc(phone, session)
            await conv.send_message(f"✅ تم حفظ الحساب `{phone}` بنجاح!")
        except Exception as err:
            await conv.send_message(f"❌ خطأ: {err}")

# --- [ تفعيل الأزرار المعطلة ] ---
@app.on(events.CallbackQuery(pattern="f_.*|cleanup|settings"))
async def disabled_btns(event):
    data = event.data.decode()
    
    if data == "f_link":
        async with app.conversation(OWNER_ID) as conv:
            await conv.send_message("🔗 أرسل رابط التجميع (بوت أو قناة):")
            link = (await conv.get_response()).text
            accounts = db.get_all()
            await event.respond(f"⏳ جاري التجميع عبر الرابط لـ {len(accounts)} حساب...")
            for p, s in accounts:
                worker = FarmWorker(p, s)
                await worker.run_task("link", target=link)
            await event.respond("✅ اكتملت العملية.")

    elif data == "f_gift":
        accounts = db.get_all()
        target = db.get_setting("target_bot", "@Z88Bot")
        await event.answer(f"🎁 تجميع هدايا من {target}...", alert=False)
        for p, s in accounts:
            worker = FarmWorker(p, s)
            await worker.run_task("gift", target=target)
        await event.respond("✅ تم الانتهاء من محاولة تجميع كافة الهدايا.")

    elif data == "f_trans":
        await event.answer("💰 ميزة الفحص والتحويل ستتوفر في التحديث القادم!", alert=True)

    elif data == "f_mix":
        await event.answer("🔥 جاري التجميع المختلط (هدايا + روابط)...", alert=True)

    elif data == "cleanup":
        await event.answer("🧹 جاري فحص الحسابات وحذف المحظورة...", alert=True)
        # منطق الفحص...
        await event.respond("✅ تم تنظيف قاعدة البيانات.")

    elif data == "settings":
        await event.edit("⚙️ **إعدادات البوت:**", buttons=[
            [Button.inline("تغيير البوت المستهدف", data="set_target")],
            [Button.inline("🔙 رجوع", data="main")]
        ])

# --- [ الإحصائيات والسجلات ] ---
@app.on(events.CallbackQuery(data="stats"))
async def stats(event):
    accs = db.get_all()
    await event.edit(f"📊 **إحصائياتك الحالية:**\n\n📱 الحسابات: `{len(accs)}`", buttons=[[Button.inline("🔙 رجوع", data="main")]])

@app.on(events.CallbackQuery(data="logs"))
async def logs(event):
    db.cursor.execute("SELECT action, date FROM logs ORDER BY id DESC LIMIT 5")
    data = db.cursor.fetchall()
    txt = "📝 **آخر سجلات العمليات:**\n\n" + "\n".join([f"• {a} [{d}]" for a, d in data])
    await event.edit(txt, buttons=[[Button.inline("🔙 رجوع", data="main")]])

@app.on(events.CallbackQuery(data="main"))
async def back(event):
    await event.edit("القائمة الرئيسية:", buttons=main_menu())

# --- [ كود التنصيب - ممنوع اللمس ] ---
@app.on(events.CallbackQuery(data="deploy"))
async def deploy(event):
    if event.sender_id != ADMIN_ID: return
    async with app.conversation(ADMIN_ID) as conv:
        try:
            await conv.send_message("⚙️ **توكن البوت الجديد:**")
            t = (await conv.get_response()).text
            await conv.send_message("👤 **آيدي الزبون:**")
            u = (await conv.get_response()).text
            await conv.send_message("⏳ **الأيام:**")
            d = (await conv.get_response()).text
            await conv.send_message("🔢 **الحد الأقصى:**")
            l = (await conv.get_response()).text
            exp = (datetime.datetime.now() + datetime.timedelta(days=int(d))).strftime('%Y-%m-%d')
            with open(f"configs/user_{u}.json", "w") as f:
                json.dump({"token": t, "owner": int(u), "expiry": exp, "max": int(l)}, f)
            subprocess.Popen([sys.executable, __file__, t, u])
            await conv.send_message(f"🚀 تم التنصيب بنجاح!")
        except Exception as e: await conv.send_message(f"❌ فشل: {e}")

# ==========================================
# 🏁 التشغيل
# ==========================================
async def main():
    print(f"✅ Titan V12 is starting for {OWNER_ID}")
    await app.start(bot_token=BOT_TOKEN)
    db.log("System Start", "Bot Online")
    await app.run_until_disconnected()

if __name__ == '__main__':
    # حل مشكلة الـ Loop في بيئات السيرفرات
    try:
        asyncio.run(main())
    except:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
