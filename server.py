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
# 🛑 المرحلة 1: المكتبات والاعتمادات
# ==========================================
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        StartBotRequest, GetHistoryRequest, GetBotCallbackAnswerRequest, SendMessageRequest
    )
    from telethon.tl.functions.channels import JoinChannelRequest
    from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
except ImportError:
    os.system("pip install telethon")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==========================================
# 🛑 المرحلة 2: الإعدادات الثابتة
# ==========================================
API_ID = 39719802  
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'  
ADMIN_ID = 8504553407 

IS_SUB_BOT = len(sys.argv) > 2
BOT_TOKEN = sys.argv[1] if IS_SUB_BOT else "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY"
OWNER_ID = int(sys.argv[2]) if IS_SUB_BOT else ADMIN_ID

for f in ['data', 'sessions', 'configs', 'logs']:
    if not os.path.exists(f): os.makedirs(f)

# ==========================================
# 📊 المرحلة 3: إدارة البيانات
# ==========================================
class TitanDB:
    def __init__(self, uid):
        self.db_path = f"data/titan_v26_{uid}.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._setup()

    def _setup(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, session TEXT, points INTEGER DEFAULT 0)''')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS activity (act TEXT, time TEXT)')
        self.conn.commit()

    def add_acc(self, p, s):
        self.cursor.execute("INSERT OR REPLACE INTO accounts (phone, session) VALUES (?, ?)", (p, s))
        self.conn.commit()

    def get_accs(self):
        self.cursor.execute("SELECT phone, session FROM accounts")
        return self.cursor.fetchall()

    def log(self, text):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.cursor.execute("INSERT INTO activity VALUES (?, ?)", (text, now))
        self.conn.commit()

db = TitanDB(OWNER_ID)

# ==========================================
# 🧠 المرحلة 4: معالجة تسجيل الدخول بالرقم
# ==========================================
async def login_by_phone(event):
    async with app.conversation(OWNER_ID) as conv:
        await conv.send_message("📞 **أرسل رقم الهاتف مع رمز الدولة (مثال: +96477...)**")
        phone = (await conv.get_response()).text.strip()
        
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        
        try:
            sent = await client.send_code_request(phone)
            await conv.send_message("📩 **وصلك كود التحقق. أرسله الآن:**")
            code = (await conv.get_response()).text.strip()
            
            try:
                await client.sign_in(phone, code, password=None)
            except SessionPasswordNeededError:
                await conv.send_message("🔐 **الحساب محمي بكلمة سر. أرسلها الآن:**")
                pwd = (await conv.get_response()).text.strip()
                await client.sign_in(password=pwd)
            
            # حفظ الجلسة
            session_str = client.session.save()
            db.add_acc(phone, session_str)
            await conv.send_message(f"✅ تم تسجيل دخول `{phone}` بنجاح!")
            db.log(f"Login: {phone}")
            
        except Exception as e:
            await conv.send_message(f"❌ فشل: {str(e)}")
        finally:
            await client.disconnect()

# ==========================================
# ⌨️ المرحلة 5: الواجهة
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
    if not IS_SUB_BOT: btns.append([Button.inline("🛠 تنصيب بوت لزبون (مطور)", data="deploy")])
    return btns

app = TelegramClient(f"sessions/main_{OWNER_ID}", API_ID, API_HASH)

@app.on(events.NewMessage(pattern='/start'))
async def start(e):
    if e.sender_id in [OWNER_ID, ADMIN_ID]:
        await e.respond("🔱 **Titan Ultimate V26**\nجميع الأزرار مفعلة بالكامل.", buttons=main_menu())

@app.on(events.CallbackQuery)
async def callback_manager(event):
    data = event.data.decode()
    
    if data == "add_p":
        await login_by_phone(event)
    
    elif data == "send_tool":
        # إنشاء الملف فوراً قبل الإرسال لضمان وجوده
        tool_code = """
import os, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
print("Titan Session Extractor")
API_ID = 39719802
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\\nYour Session:\\n", client.session.save())
        input("\\nPress Enter...")
if __name__ == "__main__": asyncio.run(main())
"""
        with open("Titan_Extractor.py", "w", encoding="utf-8") as f:
            f.write(tool_code)
        await event.client.send_file(event.chat_id, "Titan_Extractor.py", caption="🛠 أداة استخراج السيشن.")
        db.log("Sent Tool")

    elif data == "stats":
        accs = db.get_accs()
        await event.edit(f"📊 الحسابات: `{len(accs)}`", buttons=[[Button.inline("🔙 رجوع", data="main")]])

    elif data == "main":
        await event.edit("القائمة الرئيسية:", buttons=main_menu())

# ==========================================
# 🛑 كود التنصيب (لا تلمسه نهائياً)
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
