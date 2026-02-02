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
# 🛑 المرحلة 1: جلب المكتبات ومعالجة فقدانها
# ==============================================================================
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        StartBotRequest, GetHistoryRequest, GetBotCallbackAnswerRequest, SendMessageRequest
    )
    from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
    from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError
except ImportError:
    os.system("pip install telethon")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==============================================================================
# 🛑 المرحلة 2: إعدادات الاتصال والهوية
# ==============================================================================
API_ID = 39719802  
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'  
ADMIN_ID = 8504553407 

IS_SUB_BOT = len(sys.argv) > 2
BOT_TOKEN = sys.argv[1] if IS_SUB_BOT else "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY"
OWNER_ID = int(sys.argv[2]) if IS_SUB_BOT else ADMIN_ID

# تهيئة المسارات المجلدات الضرورية
for folder in ['data', 'sessions', 'configs', 'logs']:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ==============================================================================
# 📊 المرحلة 3: نظام إدارة البيانات المتقدم (SQLite Storage)
# ==============================================================================
class TitanDataManager:
    def __init__(self, user_id):
        self.db_path = f"data/titan_v27_{user_id}.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._setup_tables()

    def _setup_tables(self):
        # جدول الحسابات
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, 
            session TEXT, 
            points INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active')''')
        
        # جدول الإعدادات العامة
        self.cursor.execute('CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, val TEXT)')
        
        # جدول السجلات
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            task TEXT, 
            timestamp TEXT)''')
        
        self.conn.commit()

    def add_account(self, phone, session):
        self.cursor.execute("INSERT OR REPLACE INTO accounts (phone, session) VALUES (?, ?)", (phone, session))
        self.conn.commit()

    def get_accounts(self):
        self.cursor.execute("SELECT phone, session, points FROM accounts")
        return self.cursor.fetchall()

    def delete_account(self, phone):
        self.cursor.execute("DELETE FROM accounts WHERE phone=?", (phone,))
        self.conn.commit()

    def log_action(self, action):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO logs (task, timestamp) VALUES (?, ?)", (action, now))
        self.conn.commit()

db = TitanDataManager(OWNER_ID)

# ==============================================================================
# 🧠 المرحلة 4: محرك تسجيل الدخول والمهام البرمجية
# ==============================================================================
class TitanProEngine:
    @staticmethod
    async def login_via_phone(client_bot, owner_id):
        """نظام تسجيل الدخول التفاعلي عبر رقم الهاتف."""
        async with client_bot.conversation(owner_id) as conv:
            try:
                await conv.send_message("📞 **أرسل رقم الهاتف (مع رمز الدولة):**\nمثال: `+9647700000000`")
                phone = (await conv.get_response()).text.strip()
                
                temp_client = TelegramClient(StringSession(), API_ID, API_HASH)
                await temp_client.connect()
                
                send_code = await temp_client.send_code_request(phone)
                await conv.send_message("📩 **وصلك كود من تليجرام، أرسله هنا:**")
                code = (await conv.get_response()).text.strip()
                
                try:
                    await temp_client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    await conv.send_message("🔐 **الحساب محمي بالتحقق الثنائي، أرسل كلمة السر:**")
                    password = (await conv.get_response()).text.strip()
                    await temp_client.sign_in(password=password)
                
                new_session = temp_client.session.save()
                db.add_account(phone, new_session)
                db.log_action(f"إضافة حساب برقم: {phone}")
                await conv.send_message(f"✅ تم ربط الحساب `{phone}` بنجاح!")
                await temp_client.disconnect()
            except Exception as e:
                await conv.send_message(f"❌ خطأ أثناء التسجيل: {str(e)}")

    @staticmethod
    async def perform_task(session, task_type, target):
        """تنفيذ المهام (تجميع روابط، هدايا، قنوات)."""
        client = TelegramClient(StringSession(session), API_ID, API_HASH)
        try:
            await client.connect()
            if not await client.is_user_authorized(): return False
            
            if task_type == "join":
                if "start=" in target:
                    bot_username = target.split('/')[-1].split('?')[0]
                    param = target.split('start=')[-1]
                    await client(StartBotRequest(bot_username, bot_username, param))
                else:
                    await client(JoinChannelRequest(target))
            return True
        except: return False
        finally: await client.disconnect()

# ==============================================================================
# ⌨️ المرحلة 5: واجهة المستخدم (Buttons Builder)
# ==============================================================================
def main_menu():
    btns = [
        [Button.inline("➕ إضافة حساب (رقم)", data="act_phone"), Button.inline("🔑 إضافة حساب (سيشن)", data="act_session")],
        [Button.inline("🚀 بدء تجميع (رابط)", data="act_farm"), Button.inline("🎁 تجميع هدايا", data="act_gift")],
        [Button.inline("💰 فحص وتحويل", data="act_check"), Button.inline("🔥 تجميع مختلط", data="act_mix")],
        [Button.inline("📊 إحصائياتي", data="act_stats"), Button.inline("🧹 تنظيف الحسابات", data="act_clean")],
        [Button.inline("⚙️ الإعدادات", data="act_settings"), Button.inline("📝 السجلات", data="act_logs")],
        [Button.inline("🛠 أداة استخراج السيشن", data="act_tool")],
        [Button.url("👨‍💻 المطور", "https://t.me/G_6_W")]
    ]
    if not IS_SUB_BOT:
        btns.append([Button.inline("🛠 تنصيب بوت لزبون (مطور)", data="deploy")])
    return btns

# ==============================================================================
# ⚡ المرحلة 6: النواة والتحكم بالبوت
# ==============================================================================
app = TelegramClient(f"sessions/titan_{OWNER_ID}", API_ID, API_HASH)

@app.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id in [OWNER_ID, ADMIN_ID]:
        await event.respond("🔱 **Titan Ultimate V27**\nنظام الإدارة الشامل جاهز للعمل.", buttons=main_menu())

@app.on(events.CallbackQuery)
async def central_callback_handler(event):
    data = event.data.decode()
    sender = event.sender_id
    if sender not in [OWNER_ID, ADMIN_ID]: return

    # --- معالج أداة استخراج السيشن ---
    if data == "act_tool":
        await event.answer("⏳ جاري إنشاء الأداة...", alert=False)
        tool_content = """
import os, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
print("🚀 Titan Extractor V27")
API_ID = 39719802
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\\nإليك كود السيشن:\\n", client.session.save())
        input("\\nاضغط Enter للخروج...")
if __name__ == "__main__": asyncio.run(main())
"""
        file_path = f"extractor_{sender}.py"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(tool_content)
        await event.client.send_file(event.chat_id, file_path, caption="🛠 **أداة استخراج السيشن**\nقم بتشغيلها على جهازك لاستخراج الكود.")
        db.log_action("طلب أداة السيشن")

    # --- معالج إضافة حساب بالرقم ---
    elif data == "act_phone":
        await TitanProEngine.login_via_phone(app, sender)

    # --- معالج إضافة حساب بالسيشن ---
    elif data == "act_session":
        async with app.conversation(sender) as conv:
            await conv.send_message("🔑 **أرسل كود السيشن المباشر:**")
            s_code = (await conv.get_response()).text.strip()
            # فحص سريع
            test = TelegramClient(StringSession(s_code), API_ID, API_HASH)
            try:
                await test.connect()
                me = await test.get_me()
                db.add_account(me.phone, s_code)
                await conv.send_message(f"✅ تم إضافة الحساب `{me.phone}`")
            except: await conv.send_message("❌ السيشن غير صالح.")
            finally: await test.disconnect()

    # --- معالج الإحصائيات ---
    elif data == "act_stats":
        accounts = db.get_accounts()
        txt = f"📊 **إحصائيات المزرعة:**\n\n📱 الحسابات: `{len(accounts)}`"
        await event.edit(txt, buttons=[[Button.inline("🔙 رجوع", data="back_main")]])

    # --- معالج التجميع ---
    elif data == "act_farm":
        async with app.conversation(sender) as conv:
            await conv.send_message("🔗 **أرسل الرابط المطلوب تجميعه:**")
            link = (await conv.get_response()).text.strip()
            accs = db.get_accounts()
            await event.respond(f"🚀 بدء التجميع لـ {len(accs)} حساب...")
            for p, s, pt in accs:
                await TitanProEngine.perform_task(s, "join", link)
            await event.respond("✅ اكتملت المهمة بنجاح.")

    # --- معالج السجلات ---
    elif data == "act_logs":
        db.cursor.execute("SELECT task, timestamp FROM logs ORDER BY id DESC LIMIT 10")
        logs = db.cursor.fetchall()
        msg = "📝 **آخر 10 عمليات:**\n\n" + "\n".join([f"• {l[0]} | {l[1]}" for l in logs])
        await event.edit(msg, buttons=[[Button.inline("🔙 رجوع", data="back_main")]])

    # --- معالج العودة ---
    elif data == "back_main":
        await event.edit("القائمة الرئيسية:", buttons=main_menu())

# ==============================================================================
# 🛑 المرحلة 7: كود التنصيب للزبائن (لا يتم تعديله)
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
# 🏁 المرحلة 8: إقلاع المحرك
# ==============================================================================
if __name__ == '__main__':
    print(f"--- Titan Ultimate V27 Core Activated for {OWNER_ID} ---")
    app.start(bot_token=BOT_TOKEN)
    app.run_until_disconnected()
