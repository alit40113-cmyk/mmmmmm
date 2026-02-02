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
        StartBotRequest, ReadHistoryRequest, GetHistoryRequest, 
        GetBotCallbackAnswerRequest, SendMessageRequest
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
folders = ['data', 'sessions', 'configs', 'logs']
for folder in folders:
    if not os.path.exists(folder): os.makedirs(folder)

# ==========================================
# 📊 محرك قاعدة البيانات المطور (تم إصلاح الخطأ هنا)
# ==========================================
class DatabaseManager:
    def __init__(self, user_id):
        self.db_path = f"data/titan_v23_{user_id}.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._setup()

    def _setup(self):
        # إنشاء جدول الحسابات
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, 
            session_str TEXT, 
            points INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # إنشاء جدول الإعدادات
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        
        # إصلاح السطر الذي سبب الخطأ (استخدام Triple Quotes للنصوص الطويلة)
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            action TEXT, 
            date TEXT)''')
        
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

    def add_log(self, action):
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cursor.execute("INSERT INTO activity_logs (action, date) VALUES (?, ?)", (action, dt))
        self.conn.commit()

db = DatabaseManager(OWNER_ID)

# ==========================================
# 🧠 نظام التحقق والعمليات
# ==========================================
class TitanCore:
    @staticmethod
    async def verify_session(session_str):
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        try:
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                return True, me.phone
            return False, None
        except:
            return False, None
        finally:
            await client.disconnect()

# ==========================================
# ⌨️ واجهة التحكم
# ==========================================
def main_menu():
    btns = [
        [Button.inline("➕ إضافة حساب (رقم)", data="add_p"), Button.inline("🔑 إضافة حساب (سيشن)", data="add_s")],
        [Button.inline("🚀 بدء تجميع (رابط)", data="f_link"), Button.inline("🎁 تجميع هدايا", data="f_gift")],
        [Button.inline("💰 فحص وتحويل", data="f_trans"), Button.inline("🔥 تجميع مختلط", data="f_mix")],
        [Button.inline("📊 إحصائياتي", data="stats"), Button.inline("🧹 تنظيف الحسابات", data="cleanup")],
        [Button.inline("⚙️ الإعدادات", data="settings"), Button.inline("📝 السجلات", data="logs")],
        [Button.inline("🛠 أداة استخراج السيشن", data="send_tool")],
        [Button.url("👨‍💻 المطور", "https://t.me/G_6_W")]
    ]
    if not IS_SUB_BOT:
        btns.append([Button.inline("🛠 تنصيب بوت لزبون (مطور)", data="deploy")])
    return btns

# ==========================================
# ⚡ معالجة الفعاليات
# ==========================================
app = TelegramClient(f"sessions/bot_{OWNER_ID}", API_ID, API_HASH)

@app.on(events.NewMessage(pattern='/start'))
async def start(e):
    if e.sender_id in [OWNER_ID, ADMIN_ID]:
        db.add_log("فتح القائمة الرئيسية")
        await e.respond("🔱 **Titan Ultimate V23**\nتم إصلاح كافة الأخطاء وتفعيل النظام.", buttons=main_menu())

@app.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    
    if data == "stats":
        accs = db.get_all()
        await event.edit(f"📊 **إحصائيات المزرعة:**\n📱 عدد الحسابات: `{len(accs)}`", buttons=[[Button.inline("🔙 رجوع", data="main")]])

    elif data == "main":
        await event.edit("القائمة الرئيسية:", buttons=main_menu())

    elif data == "logs":
        db.cursor.execute("SELECT action, date FROM activity_logs ORDER BY id DESC LIMIT 10")
        rows = db.cursor.fetchall()
        txt = "📝 **آخر السجلات:**\n\n" + "\n".join([f"• {r[0]} | {r[1]}" for r in rows])
        await event.edit(txt, buttons=[[Button.inline("🔙 رجوع", data="main")]])

    elif data == "add_s":
        async with app.conversation(OWNER_ID) as conv:
            await conv.send_message("🔑 أرسل كود السيشن للتحقق:")
            session = (await conv.get_response()).text.strip()
            ok, phone = await TitanCore.verify_session(session)
            if ok:
                db.add_acc(phone, session)
                await conv.send_message(f"✅ تم تفعيل الحساب: `{phone}`")
            else:
                await conv.send_message("❌ السيشن غير صالح.")

    elif data == "cleanup":
        await event.answer("🧹 جاري التنظيف...", alert=True)
        accs = db.get_all()
        for p, s, pt in accs:
            ok, _ = await TitanCore.verify_session(s)
            if not ok: db.remove_acc(p)
        await event.respond("✅ تم تنظيف الحسابات المعطلة.")

# ==========================================
# 🛑 كود التنصيب الأصلي (لا تغير فيه شيء)
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
