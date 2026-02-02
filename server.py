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
import subprocess
import platform
import shutil
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict

# محاولة استيراد المكتبات المتقدمة وتثبيتها آلياً
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        ImportChatInviteRequest, GetHistoryRequest, 
        StartBotRequest, GetBotCallbackAnswerRequest,
        ReadHistoryRequest, ForwardMessagesRequest
    )
    from telethon.tl.functions.channels import (
        JoinChannelRequest, LeaveChannelRequest, 
        GetFullChannelRequest, InviteToChannelRequest
    )
    from telethon.tl.types import UpdateShortMessage, ReplyInlineMarkup
except ImportError:
    print("📦 جاري تثبيت المكتبات المفقودة للوصول للضخامة المطلوبة...")
    os.system("pip install telethon aiohttp requests colorama")
    os.execv(sys.executable, [sys.executable] + sys.argv)

from colorama import Fore, Style, init
init(autoreset=True)

# ==========================================
# 🛑 GLOBAL SETTINGS & SYSTEM CONSTANTS
# ==========================================

API_ID = 39719802  # استبدله بآيديك
API_HASH = '032a5697fcb9f3beeab8005d6601bde9' # استبدله بهاشك
ADMIN_ID = 8504553407 # آيديك كمطور
MAIN_BOT_TOKEN = "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY" # توكن البوت الرئيسي

IS_SUB_BOT = len(sys.argv) > 2
CURRENT_TOKEN = sys.argv[1] if IS_SUB_BOT else MAIN_BOT_TOKEN
OWNER_ID = int(sys.argv[2]) if IS_SUB_BOT else ADMIN_ID

# 

# ==========================================
# 💾 ADVANCED DATA ARCHITECTURE (SQLITE3)
# ==========================================

class Schema:
    USERS = """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                plan TEXT DEFAULT 'free',
                max_accs INTEGER DEFAULT 10,
                expiry DATE,
                target_bot TEXT DEFAULT '@Z88Bot',
                delay INTEGER DEFAULT 15,
                min_payout INTEGER DEFAULT 100
              )"""
    
    ACCOUNTS = """CREATE TABLE IF NOT EXISTS accounts (
                    phone TEXT PRIMARY KEY,
                    session TEXT NOT NULL,
                    owner_id INTEGER,
                    status TEXT DEFAULT 'active',
                    points INTEGER DEFAULT 0,
                    proxy TEXT,
                    last_check TIMESTAMP,
                    FOREIGN KEY(owner_id) REFERENCES users(user_id)
                  )"""
    
    LOGS = """CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                message TEXT,
                type TEXT,
                created_at TIMESTAMP
              )"""

class CoreDatabase:
    def __init__(self):
        self.db_path = f"data/core_{OWNER_ID}.db"
        if not os.path.exists('data'): os.makedirs('data')
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(Schema.USERS)
        cursor.execute(Schema.ACCOUNTS)
        cursor.execute(Schema.LOGS)
        self.conn.commit()

    def add_account(self, phone, session, owner):
        try:
            self.conn.execute("INSERT OR REPLACE INTO accounts (phone, session, owner_id, last_check) VALUES (?,?,?,?)",
                             (phone, session, owner, datetime.datetime.now()))
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"DB Error: {e}")
            return False

    def get_stats(self, owner_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE owner_id=?", (owner_id,))
        acc_count = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(points) FROM accounts WHERE owner_id=?", (owner_id,))
        points = cursor.fetchone()[0] or 0
        return acc_count, points

db = CoreDatabase()

# ==========================================
# 🛡️ ANTI-BAN & PROXY ROTATION SYSTEM
# ==========================================

class ProxyManager:
    """نظام إدارة البروكسي لمنع حظر الآي بي عند التعامل مع مئات الحسابات"""
    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []
    
    def get_random_proxy(self):
        if not self.proxies: return None
        p = random.choice(self.proxies).split(':')
        return {
            'proxy_type': 'socks5',
            'addr': p[0],
            'port': int(p[1]),
            'username': p[2] if len(p) > 2 else None,
            'password': p[3] if len(p) > 3 else None,
        }

# ==========================================
# 🧠 ARTIFICIAL INTELLIGENCE - MESSAGE PARSER
# ==========================================

class TitanAI:
    """محرك لتحليل رسائل البوتات وتخطي الحماية"""
    @staticmethod
    def parse_complex_balance(text: str) -> int:
        # البحث عن أرقام بجانب كلمات مفتاحية (نقاط، رصيد، فلوس، $، points)
        patterns = [r'(\d+)\s*نقطة', r'رصيدك\s*:\s*(\d+)', r'Balance\s*:\s*(\d+)']
        for p in patterns:
            match = re.search(p, text)
            if match: return int(match.group(1))
        # fallback: استخراج أكبر رقم
        nums = [int(s) for s in re.findall(r'\d+', text.replace(',', '')) if len(s) < 10]
        return max(nums) if nums else 0

    @staticmethod
    def solve_logic_challenge(text: str) -> Optional[int]:
        """حل الأسئلة المنطقية: كم ناتج 5 زائد 12؟"""
        text = text.replace('كم ناتج', '').replace('+', ' زائد ').replace('=', '')
        nums = re.findall(r'\d+', text)
        if len(nums) >= 2:
            if 'زائد' in text or '+' in text: return int(nums[0]) + int(nums[1])
            if 'ناقص' in text or '-' in text: return int(nums[0]) - int(nums[1])
            if 'في' in text or '*' in text or 'ضرب' in text: return int(nums[0]) * int(nums[1])
        return None

# ==========================================
# 🛠️ THE WORKER ENGINE (ASYNC TASKER)
# ==========================================

class FarmWorker:
    def __init__(self, phone, session, owner_id):
        self.phone = phone
        self.session = session
        self.owner_id = owner_id
        self.client = None

    async def connect(self):
        try:
            self.client = TelegramClient(StringSession(self.session), API_ID, API_HASH, 
                                         device_model="TitanFarm V6", system_version="Linux 5.15")
            await self.client.connect()
            return await self.client.is_user_authorized()
        except Exception: return False

    async def perform_harvest(self, target_bot, mode="gift"):
        if not await self.connect(): return "offline"
        try:
            # محاكاة سلوك بشري: قراءة الرسائل السابقة
            await self.client(ReadHistoryRequest(peer=target_bot, max_id=0))
            await asyncio.sleep(random.randint(2, 5))
            
            await self.client.send_message(target_bot, "/start")
            await asyncio.sleep(3)
            
            if mode == "gift":
                msgs = await self.client.get_messages(target_bot, limit=1)
                if msgs[0].reply_markup:
                    for row in msgs[0].reply_markup.rows:
                        for btn in row.buttons:
                            if "هدية" in btn.text or "Claim" in btn.text:
                                await msgs[0].click(button=btn)
                                return "success_gift"
            return "no_action"
        except Exception as e: return str(e)
        finally: await self.client.disconnect()

# ==========================================
# 🎮 ADVANCED UI & BUTTONS
# ==========================================

class Interface:
    @staticmethod
    def main_menu(user_id):
        is_admin = (user_id == ADMIN_ID)
        btns = [
            [Button.inline("📱 إضافة رقم (تلقائي)", data="add_auto"), Button.inline("🔑 إضافة سيشن", data="add_sess")],
            [Button.inline("🚀 بدء التجميع الشامل", data="farm_all")],
            [Button.inline("🔗 تجميع رابط", data="farm_link"), Button.inline("🎁 الهدايا اليومية", data="farm_gift")],
            [Button.inline("💰 فحص وتحويل النقاط", data="transfer_all")],
            [Button.inline("📊 الإحصائيات", data="stats"), Button.inline("⚙️ الإعدادات", data="settings")],
            [Button.inline("🧹 تنظيف الحسابات", data="cleanup")]
        ]
        if is_admin and not IS_SUB_BOT:
            btns.append([Button.inline("🛠 تنصيب بوت لزبون جديد", data="deploy_client")])
        return btns

# ==========================================
# ⚡ BOT CORE LOGIC
# ==========================================

bot = TelegramClient(f'core_{OWNER_ID}', API_ID, API_HASH).start(bot_token=CURRENT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    # التحقق من الاشتراك المنتهي
    config_path = f"configs/user_{OWNER_ID}.json"
    if IS_SUB_BOT and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            conf = json.load(f)
            expiry = datetime.datetime.strptime(conf['expiry'], '%Y-%m-%d')
            if datetime.datetime.now() > expiry:
                return await event.respond("⚠️ انتهى اشتراكك! يرجى التواصل مع المطور للتجديد.")

    await event.respond(
        f"🔱 **نظام التجميع العملاق Titan v6**\n"
        f"--- --- --- --- ---\n"
        f"👤 المالك: `{OWNER_ID}`\n"
        f"📅 الحالة: `نشط ✅`\n"
        f"🤖 النسخة: `Enterprise Edition`",
        buttons=Interface.main_menu(event.sender_id)
    )

@bot.on(events.CallbackQuery(data="deploy_client"))
async def deploy_handler(event):
    if event.sender_id != ADMIN_ID: return
    
    async with bot.conversation(ADMIN_ID) as conv:
        await conv.send_message("⚙️ **أرسل توكن بوت الزبون:**")
        token = (await conv.get_response()).text
        await conv.send_message("👤 **أرسل آيدي الزبون:**")
        uid = (await conv.get_response()).text
        await conv.send_message("⏳ **عدد أيام الاشتراك:**")
        days = (await conv.get_response()).text
        await conv.send_message("🔢 **الحد الأقصى للأرقام:**")
        limit = (await conv.get_response()).text

        exp = (datetime.datetime.now() + datetime.timedelta(days=int(days))).strftime('%Y-%m-%d')
        
        # حفظ الإعدادات
        if not os.path.exists('configs'): os.makedirs('configs')
        with open(f"configs/user_{uid}.json", 'w') as f:
            json.dump({"expiry": exp, "limit": int(limit), "token": token}, f)

        # تشغيل العملية
        subprocess.Popen([sys.executable, sys.executable, token, uid])
        await conv.send_message(f"✅ تم التنصيب بنجاح لآيدي `{uid}`\nينتهي في `{exp}`")

@bot.on(events.CallbackQuery(data="stats"))
async def stats_handler(event):
    accs, points = db.get_stats(OWNER_ID)
    await event.edit(
        f"📊 **إحصائيات مزرعتك:**\n\n"
        f"📱 عدد الحسابات: `{accs}`\n"
        f"💰 مجموع النقاط: `{points}`\n"
        f"🕒 آخر فحص: `{datetime.datetime.now().strftime('%H:%M')}`",
        buttons=[[Button.inline("🔙 رجوع", data="main")]]
    )

@bot.on(events.CallbackQuery(data="main"))
async def main_back(event):
    await event.edit("القائمة الرئيسية:", buttons=Interface.main_menu(event.sender_id))

# ==========================================
# 🌀 BACKGROUND ENGINE (SCHEDULER)
# ==========================================

async def global_auto_farm():
    """محرك يعمل في الخلفية لمراقبة الحسابات وتجميع الهدايا تلقائياً"""
    while True:
        try:
            # كود التجميع التلقائي هنا (يعمل كل 12 ساعة)
            await asyncio.sleep(43200) 
        except Exception: pass

# ==========================================
# 🚀 INITIALIZATION
# ==========================================

if __name__ == '__main__':
    print(f"{Fore.CYAN}{'='*40}")
    print(f"{Fore.GREEN}TITAN FARMING SYSTEM IS STARTING...")
    print(f"{Fore.YELLOW}Owner ID: {OWNER_ID}")
    print(f"{Fore.CYAN}{'='*40}")
    
    loop = asyncio.get_event_loop()
    loop.create_task(global_auto_farm())
    bot.run_until_disconnected()
