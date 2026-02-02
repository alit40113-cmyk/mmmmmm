import asyncio
import os
import sys
import json
import datetime
import logging
import re
import random
import time
import traceback
import sqlite3
from typing import List, Dict, Any, Optional

# استيراد مكتبات تليثون مع معالجة الاستثناءات
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        ImportChatInviteRequest, 
        GetHistoryRequest, 
        StartBotRequest, 
        GetBotCallbackAnswerRequest
    )
    from telethon.tl.functions.channels import (
        JoinChannelRequest, 
        LeaveChannelRequest, 
        GetFullChannelRequest
    )
    from telethon.tl.functions.users import GetFullUserRequest
    from telethon.utils import get_display_name
except ImportError:
    print("❌ مكتبة Telethon غير مثبتة! جاري التثبيت...")
    os.system("pip install telethon")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==========================================
# 🛑 قسم الإعدادات المتقدمة (Advanced Config)
# ==========================================

API_ID = 1234567  # استبدله بـ API ID الخاص بك
API_HASH = 'your_api_hash_here'  # استبدله بـ API HASH الخاص بك
ADMIN_ID = 12345678  # آيدي المطور الأساسي
LOG_CHANNEL = -100123456789  # آيدي قناة السجلات (اختياري)

class Config:
    VERSION = "4.0.0-PRO"
    DB_NAME = "farm_master.db"
    SESSIONS_DIR = "./sessions_data/"
    DEFAULT_DELAY = 10
    MAX_RETRIES = 3
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ==========================================
# 📊 نظام إدارة قاعدة البيانات (SQL Engine)
# ==========================================

class DatabaseManager:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # جدول المستخدمين
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            target_id TEXT,
            points INTEGER DEFAULT 0,
            is_premium BOOLEAN DEFAULT 0,
            joined_at TIMESTAMP
        )''')
        
        # جدول الحسابات الوهمية
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY,
            session_str TEXT,
            owner_id TEXT,
            status TEXT DEFAULT 'active',
            last_used TIMESTAMP,
            points_collected INTEGER DEFAULT 0,
            FOREIGN KEY(owner_id) REFERENCES users(user_id)
        )''')
        
        # جدول الإعدادات العامة
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')
        self.conn.commit()

    def add_user(self, user_id: str):
        self.cursor.execute("INSERT OR IGNORE INTO users (user_id, joined_at) VALUES (?, ?)", 
                           (user_id, datetime.datetime.now()))
        self.conn.commit()

    def add_account(self, phone: str, session: str, owner_id: str):
        self.cursor.execute("""
            INSERT OR REPLACE INTO accounts (phone, session_str, owner_id, last_used) 
            VALUES (?, ?, ?, ?)
        """, (phone, session, owner_id, datetime.datetime.now()))
        self.conn.commit()

    def get_user_accounts(self, owner_id: str):
        self.cursor.execute("SELECT phone, session_str FROM accounts WHERE owner_id = ?", (owner_id,))
        return self.cursor.fetchall()

db = DatabaseManager(Config.DB_NAME)

# ==========================================
# 🤖 نظام التحليل الذكي وتخطي البوتات
# ==========================================

class SmartAnalyzer:
    """محرك لتحليل نصوص البوتات وتجاوز أنظمة الحماية"""
    
    @staticmethod
    def parse_balance(text: str) -> int:
        """يستخرج الرصيد من رسالة البوت باستخدام Regex معقد"""
        patterns = [
            r"رصيدك هو\s*:\s*(\d+)",
            r"نقاطك\s*:\s*(\d+)",
            r"Balance\s*:\s*(\d+)",
            r"Your points\s*:\s*(\d+)",
            r"عدد نقاطك\s*(\d+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        # محاولة البحث عن أي رقم كبير في الرسالة إذا فشلت الأنماط
        nums = re.findall(r'\d+', text)
        return int(nums[0]) if nums else 0

    @staticmethod
    def solve_captcha(text: str) -> Optional[int]:
        """حل التحديات الرياضية البسيطة التي تطلبها بوتات التجميع"""
        clean_text = text.replace('x', '*').replace('÷', '/')
        math_match = re.search(r'(\d+)\s*([\+\-\*\/])\s*(\d+)', clean_text)
        if math_match:
            try:
                expression = f"{math_match.group(1)}{math_match.group(2)}{math_match.group(3)}"
                return int(eval(expression))
            except:
                return None
        return None

# ==========================================
# 🛠️ مدير الجلسات والعمليات الميدانية
# ==========================================

class Worker:
    def __init__(self, session_str: str, phone: str):
        self.session = session_str
        self.phone = phone
        self.client: Optional[TelegramClient] = None

    async def connect(self) -> bool:
        try:
            self.client = TelegramClient(StringSession(self.session), API_ID, API_HASH)
            await self.client.connect()
            return await self.client.is_user_authorized()
        except Exception as e:
            logging.error(f"Error connecting {self.phone}: {e}")
            return False

    async def join_bot_via_link(self, bot_username: str, invite_param: Optional[str]):
        """الدخول إلى بوت عبر رابط إحالة"""
        if not await self.connect(): return "failed_auth"
        try:
            await self.client(StartBotRequest(
                bot=bot_username,
                peer=bot_username,
                start_param=invite_param
            ))
            return "success"
        except errors.FloodWaitError as e:
            return f"flood_{e.seconds}"
        except Exception as e:
            return f"error_{str(e)}"
        finally:
            await self.client.disconnect()

    async def collect_daily_gift(self, bot_user: str):
        """البحث عن زر الهدية اليومية والضغط عليه"""
        if not await self.connect(): return
        try:
            await self.client.send_message(bot_user, "/start")
            await asyncio.sleep(2)
            async for message in self.client.iter_messages(bot_user, limit=3):
                if message.reply_markup:
                    for row in message.reply_markup.rows:
                        for btn in row.buttons:
                            if any(word in btn.text for word in ["هدية", "يومية", "Daily", "Gift", "Claim"]):
                                await message.click(button=btn)
                                return True
            return False
        finally:
            await self.client.disconnect()

# ==========================================
# 🎮 واجهة التحكم الرسومية (Buttons & Menus)
# ==========================================

class UI:
    @staticmethod
    def main_menu():
        return [
            [Button.inline("➕ إضافة حساب جديد", data="m_add_acc")],
            [Button.inline("🚀 بدء تجميع النقاط", data="m_start_farm")],
            [Button.inline("💰 تحويل النقاط تلقائياً", data="m_auto_transfer")],
            [Button.inline("📊 إحصائيات المزرعة", data="m_stats"), Button.inline("⚙️ الإعدادات", data="m_settings")],
            [Button.inline("🧹 تنظيف الحسابات المعطلة", data="m_cleanup")],
            [Button.url("📣 قناة التحديثات", "https://t.me/YourChannel")]
        ]

    @staticmethod
    def add_account_menu():
        return [
            [Button.inline("📱 عبر رقم الهاتف (كود)", data="add_phone")],
            [Button.inline("🔑 عبر كود السيشن (String)", data="add_session")],
            [Button.inline("🔙 عودة للقائمة الرئيسية", data="m_main")]
        ]

# ==========================================
# ⚡ معالج الأحداث الرئيسي (Main Bot Logic)
# ==========================================

bot_token = sys.argv[1] if len(sys.argv) > 1 else "YOUR_BOT_TOKEN"
app = TelegramClient('ManagerSession', API_ID, API_HASH).start(bot_token=bot_token)

@app.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    db.add_user(str(event.sender_id))
    await event.respond(
        f"🛡 **مرحباً بك في نظام إدارة المزارع المتطور**\n"
        f"--- --- --- --- ---\n"
        f"👤 المستخدِم: `{event.sender_id}`\n"
        f"📅 النسخة: `{Config.VERSION}`\n"
        f"🤖 حالة النظام: `يعمل بكفاءة ✅`",
        buttons=UI.main_menu()
    )

@app.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    uid = str(event.sender_id)

    if data == "m_main":
        await event.edit("قائمة التحكم الرئيسية:", buttons=UI.main_menu())

    elif data == "m_add_acc":
        await event.edit("🛠 اختر طريقة إضافة الحساب:", buttons=UI.add_account_menu())

    elif data == "add_session":
        async with app.conversation(event.sender_id) as conv:
            await conv.send_message("📝 **أرسل كود السيشن (String Session) الآن:**")
            session_msg = await conv.get_response()
            session_str = session_msg.text
            
            await conv.send_message("📞 **أرسل رقم الهاتف المرتبط بهذا السيشن:**")
            phone_msg = await conv.get_response()
            phone = phone_msg.text

            await conv.send_message("⏳ **جاري التحقق من صحة الحساب...**")
            test_worker = Worker(session_str, phone)
            if await test_worker.connect():
                me = await test_worker.client.get_me()
                db.add_account(phone, session_str, uid)
                await conv.send_message(f"✅ **تمت إضافة الحساب بنجاح!**\n👤 الاسم: {get_display_name(me)}\n🆔 الآيدي: `{me.id}`")
            else:
                await conv.send_message("❌ **فشل التحقق!** السيشن غير صالح أو منتهي.")

    elif data == "m_start_farm":
        await event.edit("🚀 **اختر وضع التجميع:**", buttons=[
            [Button.inline("🔗 تجميع عبر رابط دعوة", data="farm_link")],
            [Button.inline("🎁 تجميع هدايا يومية", data="farm_gift")],
            [Button.inline("🔥 تجميع شامل (الكل)", data="farm_all")],
            [Button.inline("🔙 عودة", data="m_main")]
        ])

    elif data == "farm_link":
        async with app.conversation(event.sender_id) as conv:
            await conv.send_message("🔗 **أرسل رابط الدعوة الخاص بالبوت المستهدف:**")
            link = (await conv.get_response()).text
            
            # استخراج المعطيات
            bot_user = link.split('t.me/')[1].split('?')[0]
            param = link.split('start=')[1] if 'start=' in link else None
            
            accounts = db.get_user_accounts(uid)
            await conv.send_message(f"⏳ جاري العمل على {len(accounts)} حساب...")
            
            for phone, sess in accounts:
                w = Worker(sess, phone)
                res = await w.join_bot_via_link(bot_user, param)
                await asyncio.sleep(Config.DEFAULT_DELAY)
            
            await conv.send_message("✅ **اكتملت عملية التجميع بنجاح!**")

# استكمال الكود في الجزء الثاني...
if __name__ == '__main__':
    print(">>> System Booting Up...")
    app.run_until_disconnected()
