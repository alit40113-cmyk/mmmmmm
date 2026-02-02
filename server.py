# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE GIGA-TITAN FACTORY - SUPREME ARCHITECTURE V50.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- نظام تشفير وحماية السيشنات من الطرد (Anti-Termination).
- محاكاة دقيقة لبيانات الأجهزة الرسمية (Device Mimicry).
- تخطي اشتراك إجباري متطور (حتى 25 قناة/بوت).
- إدارة كاملة عبر لوحة تحكم Telegram Bot API.
- سجلات حية (Live Logging) لجميع العمليات.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import re
import sys
import json
import time
import asyncio
import logging
import datetime
import random
import platform
import string
from dataclasses import dataclass, asdict

# --- [ فحص وتثبيت المكتبات ] ---
try:
    from telethon import TelegramClient, events, Button, functions, types
    from telethon.sessions import StringSession
    from telethon.errors import *
    from telethon.tl.functions.messages import GetHistoryRequest, StartBotRequest
    from telethon.tl.functions.channels import JoinChannelRequest
    from telethon.tl.types import KeyboardButtonUrl, InlineKeyboardButtonUrl
except ImportError:
    print("🚀 Installing High-Performance Libraries...")
    os.system(f'{sys.executable} -m pip install telethon')
    from telethon import TelegramClient, events, Button, functions, types
    from telethon.sessions import StringSession

# --- [ إعدادات السجلات الاحترافية ] ---
class CustomFormatter(logging.Formatter):
    """منسق سجلات ملون لاحترافية السورس"""
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

logger = logging.getLogger("GigaTitan")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

# --- [ الثوابت الجوهرية ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

if len(sys.argv) > 2:
    BOT_TOKEN = sys.argv[1]
    MASTER_ID = int(sys.argv[2])
else:
    MASTER_ID = 8504553407  
    BOT_TOKEN = '8331141429:AAGeDiqh7Wqk0fiOQMDNbPSGTuXztIP0SzA'

DB_FILE = f'giga_v50_db_{MASTER_ID}.json'

# --- [ كلاس محاكاة الأجهزة المتقدم ] ---
class HardwareProfile:
    """محاكاة أجهزة حقيقية تمنع تيليجرام من طردك"""
    PROFILES = [
        {"dm": "iPhone 15 Pro Max", "sv": "iOS 17.2.1", "av": "10.5.1"},
        {"dm": "Samsung Galaxy S24 Ultra", "sv": "Android 14", "av": "10.4.0"},
        {"dm": "Google Pixel 8 Pro", "sv": "Android 14", "av": "10.4.2"},
        {"dm": "iPad Pro M2", "sv": "iPadOS 17.1", "av": "10.3.0"},
        {"dm": "MacBook Pro M3", "sv": "macOS 14.2", "av": "4.12.3"},
        {"dm": "Windows 11 Pro", "sv": "Build 22621", "av": "4.15.0"},
        {"dm": "Xiaomi 14 Pro", "sv": "HyperOS 1.0", "av": "10.6.0"},
        {"dm": "OnePlus 12", "sv": "OxygenOS 14", "av": "10.2.1"}
    ]

    @classmethod
    def pick(cls):
        return random.choice(cls.PROFILES)

# --- [ نظام قاعدة البيانات العبقرية ] ---
class GigaDatabase:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if not os.path.exists(DB_FILE):
            initial = {
                "accounts": {},
                "settings": {
                    "target_bot": "@t06bot",
                    "ref_link": "",
                    "delay_min": 40,
                    "delay_max": 80,
                    "auto_stealth": True
                },
                "global_stats": {
                    "points_collected": 0,
                    "joins_done": 0,
                    "failed_accounts": 0
                }
            }
            self._save(initial)
            return initial
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save(self, data_to_save=None):
        target = data_to_save or self.data
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(target, f, indent=4, ensure_ascii=False)

    def update_stat(self, key):
        self.data["global_stats"][key] = self.data["global_stats"].get(key, 0) + 1
        self._save()

db_manager = GigaDatabase()

# --- [ محرك تخطي الحماية (Bypass Core) ] ---

async def titan_deep_bypass(client, target, link):
    """محرك التخطي الأكثر تعقيداً للتعامل مع بوتات التجميع الحديثة"""
    try:
        active_target = target
        # 1. تفعيل نظام الإحالة
        if "start=" in link:
            param = link.split('start=')[-1]
            bot_nick = link.split('/')[-1].split('?')[0]
            await client(StartBotRequest(bot=bot_nick, peer=bot_nick, start_param=param))
            active_target = bot_nick
            logger.info(f"🚀 Referral sequence initiated: {param}")

        # 2. دورة التخطي المتسلسلة (Deep Scan Loop)
        for i in range(25): # يدعم حتى 25 قناة اشتراك
            await client.send_message(active_target, "/start")
            await asyncio.sleep(8)
            
            history = await client(GetHistoryRequest(
                peer=active_target, limit=1, offset_date=None, 
                offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0
            ))
            
            if not history.messages or not history.messages[0].reply_markup:
                logger.info("✅ Bypass Complete: UI is clear.")
                break
            
            top_msg = history.messages[0]
            action_found = False
            
            # فحص الأزرار
            for row in top_msg.reply_markup.rows:
                for btn in row.buttons:
                    # معالجة الروابط
                    if isinstance(btn, (KeyboardButtonUrl, InlineKeyboardButtonUrl)):
                        url = btn.url
                        action_found = True
                        try:
                            clean_path = url.split('/')[-1]
                            if "joinchat" in url or "+" in url:
                                h = clean_path.replace('+', '')
                                try: await client(functions.messages.ImportChatInviteRequest(hash=h))
                                except: await client(functions.messages.CheckChatInviteRequest(hash=h))
                            else:
                                await client(JoinChannelRequest(channel=clean_path))
                            logger.info(f"🔗 Joined Channel: {clean_path}")
                        except Exception as e:
                            logger.error(f"⚠️ Join error: {str(e)[:50]}")
                    
                    # معالجة أزرار التأكيد
                    elif any(word in btn.text for word in ["تحقق", "تم", "تأكيد", "Done", "Check"]):
                        await top_msg.click(text=btn.text)
                        await asyncio.sleep(4)
                        action_found = True
            
            if not action_found:
                break
                
    except Exception as e:
        logger.error(f"❌ Critical Bypass Failure: {e}")

# --- [ نظام إدارة الجلسات الذكي (Anti-LogOut) ] ---

async def run_safe_worker(phone, account_info):
    """تشغيل الحساب بهوية محاكاة كاملة لمنع تسجيل الخروج"""
    hw = account_info.get('hw_profile') or HardwareProfile.pick()
    
    # استخدام StringSession مع بيانات جهاز فريدة
    client = TelegramClient(
        StringSession(account_info['ss']), 
        API_ID, 
        API_HASH,
        device_model=hw['dm'],
        system_version=hw['sv'],
        app_version=hw['av']
    )
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.error(f"🚫 Account {phone} is dead/banned.")
            return False
            
        # تمويه الاسم
        if db_manager.data["settings"]["auto_stealth"]:
            new_name = "".join(random.choices(string.ascii_uppercase, k=1)) + "".join(random.choices(string.ascii_lowercase, k=5))
            await client(functions.account.UpdateProfileRequest(first_name=new_name))
            
        # تشغيل التخطي
        target = db_manager.data["settings"]["target_bot"]
        ref = db_manager.data["settings"]["ref_link"]
        await titan_deep_bypass(client, target, ref)
        
        # التجميع النهائي
        await asyncio.sleep(5)
        last_msgs = await client.get_messages(target, limit=1)
        if last_msgs and last_msgs[0].reply_markup:
            for row in last_msgs[0].reply_markup.rows:
                for b in row.buttons:
                    if any(x in b.text for x in ["هدية", "يومية", "تجميع", "Claim"]):
                        await last_msgs[0].click(text=b.text)
                        db_manager.update_stat("points_collected")
                        logger.info(f"💰 Reward claimed for {phone}")
        
        await client.disconnect()
        return True
    except Exception as e:
        logger.error(f"🛠 Worker error on {phone}: {e}")
        return False

# --- [ المحرك الدوري (Main Engine) ] ---

async def giga_automation_engine():
    while True:
        logger.info("🌀 Initiating Galactic Farming Cycle...")
        data = db_manager.data
        accounts = list(data["accounts"].items())
        
        if not accounts:
            logger.warning("📭 No accounts found. Idle mode...")
            await asyncio.sleep(60)
            continue
            
        for phone, info in accounts:
            logger.info(f"⚙️ Processing: {phone} | {info['name']}")
            status = await run_safe_worker(phone, info)
            
            # تأخير عشوائي بين الحسابات لمنع كشف الـ IP
            delay = random.randint(data["settings"]["delay_min"], data["settings"]["delay_max"])
            logger.info(f"⏳ Cooling down for {delay}s...")
            await asyncio.sleep(delay)
            
        logger.info("🛌 Cycle finished. Sleeping for 24H.")
        await asyncio.sleep(86400)

# --- [ لوحة تحكم التليجرام (Giga UI) ] ---

bot = TelegramClient(f'giga_bot_{MASTER_ID}', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id != MASTER_ID: return
    
    d = db_manager.data
    s = d["global_stats"]
    
    dashboard = (
        "👑 **GIGA-TITAN SUPREME PANEL V50.0** 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 الحسابات المدمجة: `{len(d['accounts'])}` الحسابات\n"
        f"🎯 البوت المستهدف: `{d['settings']['target_bot']}`\n"
        f"🔗 الإحالة: `{d['settings']['ref_link'][:25] if d['settings']['ref_link'] else 'غير محدد'}...` \n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ تجميعات ناجحة: `{s['points_collected']}`\n"
        f"⚠️ فشل/حظر: `{s['failed_accounts']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "إدارة المنظومة الإمبراطورية:"
    )
    
    btns = [
        [Button.inline("➕ إضافة حساب (String)", "add_string"), Button.inline("🗑️ حذف حساب", "remove_acc")],
        [Button.inline("🎯 تعيين الهدف", "set_target"), Button.inline("🔗 رابط الإحالة", "set_ref")],
        [Button.inline("⚙️ الإعدادات", "config"), Button.inline("📋 كشف الحسابات", "list_all")],
        [Button.inline("📥 أداة الاستخراج", "get_tool"), Button.inline("🚀 تشغيل فوري", "force_start")],
        [Button.url("👨‍💻 المطور", "https://t.me/Tele_Sajad")]
    ]
    await event.reply(dashboard, buttons=btns)

@bot.on(events.CallbackQuery)
async def controller(event):
    if event.sender_id != MASTER_ID: return
    cmd = event.data.decode()
    
    if cmd == "add_string":
        async with bot.conversation(event.sender_id, timeout=600) as conv:
            await conv.send_message("🔑 **أرسل الـ String Session (Telethon):**")
            ss = (await conv.get_response()).text.strip()
            await conv.send_message("📱 **أرسل رقم الهاتف المرتبط (للتوثيق):**")
            ph = (await conv.get_response()).text.strip()
            
            p_msg = await conv.send_message("🛡️ جاري التوثيق وتثبيت هوية الجهاز...")
            try:
                hw = HardwareProfile.pick()
                temp = TelegramClient(StringSession(ss), API_ID, API_HASH, device_model=hw['dm'])
                await temp.connect()
                if await temp.is_user_authorized():
                    me = await temp.get_me()
                    db_manager.data["accounts"][me.phone] = {
                        "ss": ss, "name": me.first_name, "hw_profile": hw,
                        "added_at": str(datetime.datetime.now())
                    }
                    db_manager._save()
                    await p_msg.edit(f"✅ **تم الربط بنجاح!**\n👤 الاسم: {me.first_name}\n📱 الجهاز: {hw['dm']}")
                else:
                    await p_msg.edit("❌ فشل: السيشن غير صالح أو منتهي.")
                await temp.disconnect()
            except Exception as e:
                await p_msg.edit(f"⚠️ خطأ فني: {e}")

    elif cmd == "list_all":
        accs = db_manager.data["accounts"]
        if not accs: return await event.respond("📭 لا توجد حسابات.")
        out = "📋 **قائمة حسابات التايتان:**\n\n"
        for p, i in accs.items():
            out += f"• `+{p}` | {i['name']} | 📱 {i['hw_profile']['dm']}\n"
        await event.respond(out)

    elif cmd == "get_tool":
        tool_script = (
            f"from telethon import TelegramClient; import asyncio\n"
            f"API_ID = {API_ID}\nAPI_HASH = '{API_HASH}'\n"
            f"async def main():\n"
            f"    async with TelegramClient(None, API_ID, API_HASH) as client:\n"
            f"        print('\\n✅ Your Session String:\\n')\n"
            f"        print(client.session.save())\n"
            f"asyncio.run(main())"
        )
        with open("GigaExtractor.py", "w") as f: f.write(tool_script)
        await event.respond("🛠 **أداة استخراج السيشن الآمنة:**\nاستخدمها لاستخراج السيشن بنفس الـ API الخاص بالبوت لضمان عدم الطرد.", file="GigaExtractor.py")

# --- [ التشغيل النهائي للمنظومة ] ---
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # تشغيل محرك الأتمتة في الخلفية
    loop.create_task(giga_automation_engine())
    logger.info("🔥 GIGA-TITAN V50.0 HAS BEEN AWAKENED.")
    # تشغيل بوت التحكم
    bot.run_until_disconnected()
