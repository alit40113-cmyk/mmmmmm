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

# إنشاء ملف الأداة تلقائياً
EXTRACTOR_SCRIPT = "extractor.py"
with open(EXTRACTOR_SCRIPT, "w", encoding="utf-8") as f:
    f.write("""
import os, asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
print("🚀 Titan Extractor")
API_ID = 39719802
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\\n✅ Session Code:\\n")
        print(client.session.save())
        input("\\nDone...")
if __name__ == "__main__":
    asyncio.run(main())
""")

# ==========================================
# 📊 محرك قاعدة البيانات
# ==========================================
class DatabaseManager:
    def __init__(self, user_id):
        self.db_path = f"data/titan_v19_{user_id}.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._setup()

    def _setup(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, session_str TEXT, points INTEGER DEFAULT 0)''')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        self.conn.commit()

    def add_acc(self, phone, session):
        self.cursor.execute("INSERT OR REPLACE INTO accounts (phone, session_str) VALUES (?, ?)", (phone, session))
        self.conn.commit()

    def get_all(self):
        self.cursor.execute("SELECT phone, session_str, points FROM accounts")
        return self.cursor.fetchall()

    def remove_acc(self, phone):
        self.cursor.execute("DELETE FROM accounts WHERE phone=?", (phone,))
        self.conn.commit()

    def set_setting(self, key, val):
        self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(val)))
        self.conn.commit()

    def get_setting(self, key, default=None):
        self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        res = self.cursor.fetchone()
        return res[0] if res else default

db = DatabaseManager(OWNER_ID)

# ==========================================
# ⌨️ واجهة التحكم
# ==========================================
def main_menu():
    btns = [
        [Button.inline("➕ إضافة حساب (رقم)", data="add_p"), Button.inline("🔑 إضافة حساب (سيشن)", data="add_s")],
        [Button.inline("🚀 بدء تجميع (رابط)", data="f_link"), Button.inline("🎁 تجميع هدايا", data="f_gift")],
        [Button.inline("🛠 أداة استخراج السيشن", data="send_tool")],
        [Button.inline("💰 فحص وتحويل", data="f_trans"), Button.inline("🔥 تجميع مختلط", data="f_mix")],
        [Button.inline("📊 إحصائياتي", data="stats"), Button.inline("🧹 تنظيف الحسابات", data="cleanup")],
        [Button.inline("⚙️ الإعدادات", data="settings"), Button.inline("📝 السجلات", data="logs")],
        [Button.url("👨‍💻 المطور", "https://t.me/G_6_W")]
    ]
    if not IS_SUB_BOT:
        btns.append([Button.inline("🛠 تنصيب بوت لزبون (مطور)", data="deploy")])
    return btns

# ==========================================
# ⚡ النواة البرمجية
# ==========================================
app = TelegramClient(f"sessions/bot_{OWNER_ID}", API_ID, API_HASH)

@app.on(events.NewMessage(pattern='/start'))
async def start(e):
    if e.sender_id in [OWNER_ID, ADMIN_ID]:
        await e.respond("🔱 **Titan Ultimate V19**\nنظام الإدارة والتحقق جاهز.", buttons=main_menu())

# --- [ أداة السيشن ] ---
@app.on(events.CallbackQuery(data="send_tool"))
async def send_tool(event):
    await event.answer("⏳ جاري الإرسال...", alert=False)
    await event.client.send_file(event.chat_id, EXTRACTOR_SCRIPT, caption="🛠 **أداة استخراج السيشن**\nاستخدمها لاستخراج الكود بأمان.")

# --- [ إضافة سيشن مع تحقق ذكي ] ---
@app.on(events.CallbackQuery(data="add_s"))
async def add_session_verified(event):
    async with app.conversation(OWNER_ID) as conv:
        await conv.send_message("📞 **أرسل الرقم مع رمز الدولة:**")
        phone = (await conv.get_response()).text.strip()
        await conv.send_message("🔑 **أرسل كود السيشن:**")
        session = (await conv.get_response()).text.strip()
        
        status_msg = await conv.send_message("⏳ **جاري التحقق من السيشن...**")
        temp_client = TelegramClient(StringSession(session), API_ID, API_HASH)
        try:
            await temp_client.connect()
            if await temp_client.is_user_authorized():
                db.add_acc(phone, session)
                await status_msg.edit(f"✅ **تم التحقق بنجاح!** الحساب `{phone}` مضاف الآن.")
            else:
                await status_msg.edit("❌ **السيشن غير صالح أو منتهي.**")
        except:
            await status_msg.edit("❌ **خطأ في الاتصال بالحساب.**")
        finally:
            await temp_client.disconnect()

# --- [ تجميع الروابط ] ---
@app.on(events.CallbackQuery(data="f_link"))
async def link_farm(event):
    async with app.conversation(OWNER_ID) as conv:
        await conv.send_message("🔗 **أرسل الرابط أو يوزر البوت:**")
        link = (await conv.get_response()).text.strip()
        accs = db.get_all()
        await event.respond(f"🚀 **بدء التجميع بـ {len(accs)} حساب...**")
        
        success = 0
        for p, s, pt in accs:
            c = TelegramClient(StringSession(s), API_ID, API_HASH)
            try:
                await c.connect()
                if "start=" in link:
                    bot_u = link.split('/')[-1].split('?')[0]
                    param = link.split('start=')[-1]
                    await c(StartBotRequest(bot_u, bot_u, param))
                else:
                    await c(JoinChannelRequest(link))
                success += 1
            except: pass
            finally: await c.disconnect()
        await event.respond(f"📊 **النتيجة:** نجاح `{success}` من أصل `{len(accs)}`")

# --- [ تنظيف الحسابات ] ---
@app.on(events.CallbackQuery(data="cleanup"))
async def cleanup_accs(event):
    await event.answer("🧹 جاري فحص وتنظيف الحسابات الميتة...", alert=True)
    accs = db.get_all()
    dead = 0
    for p, s, pt in accs:
        c = TelegramClient(StringSession(s), API_ID, API_HASH)
        try:
            await c.connect()
            if not await c.is_user_authorized():
                db.remove_acc(p)
                dead += 1
        except:
            db.remove_acc(p)
            dead += 1
        finally: await c.disconnect()
    await event.respond(f"✅ **اكتمل التنظيف!**\nتم حذف `{dead}` حساب معطل.")

# --- [ إحصائيات وباقي الأزرار ] ---
@app.on(events.CallbackQuery(pattern="stats|main|logs|settings"))
async def others(event):
    data = event.data.decode()
    if data == "stats":
        accs = db.get_all()
        await event.edit(f"📊 **إحصائياتك:**\n📱 الحسابات: `{len(accs)}`", buttons=[[Button.inline("🔙 رجوع", data="main")]])
    elif data == "main":
        await event.edit("القائمة الرئيسية:", buttons=main_menu())

# ==========================================
# 🛑 كود التنصيب الأصلي (بدون أي تغيير) 🛑
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

if __name__ == '__main__':
    app.start(bot_token=BOT_TOKEN)
    app.run_until_disconnected()
