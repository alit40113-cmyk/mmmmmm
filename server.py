# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE IMPERIAL TITAN FACTORY - SUPREME EDITION V40.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
نظام متكامل لإدارة الحسابات، التجميع، وتخطي الحماية:
1. نظام الحماية من تسجيل الخروج (Anti-Session Termination).
2. محاكاة أجهزة حقيقية (iPhone 15, Samsung S24, Windows 11).
3. تخطي الاشتراك الإجباري المعقد (حتى 20 قناة).
4. نظام الإحالات الذكي مع دعم الروابط المشفرة.
5. نظام "صحة الحسابات" لفحص الحسابات المحظورة تلقائياً.
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
import subprocess
import platform
import random
from datetime import timedelta

# --- [ إعدادات المكتبات الأساسية ] ---
try:
    from telethon import TelegramClient, events, Button, functions, types
    from telethon.sessions import StringSession
    from telethon.errors import *
    from telethon.tl.functions.messages import GetHistoryRequest
    from telethon.tl.functions.channels import JoinChannelRequest
except ImportError:
    print("📦 Installing required libraries...")
    os.system(f'{sys.executable} -m pip install telethon')
    from telethon import TelegramClient, events, Button, functions, types
    from telethon.sessions import StringSession

# --- [ إعدادات السجلات المتقدمة ] ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[logging.FileHandler("imperial_supreme.log"), logging.StreamHandler()]
)
logger = logging.getLogger("SupremeEngine")

# --- [ الثوابت CONFIGURATION ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

if len(sys.argv) > 2:
    BOT_TOKEN = sys.argv[1]
    MASTER_ID = int(sys.argv[2])
else:
    MASTER_ID = 8504553407  
    BOT_TOKEN = '8331141429:AAGeDiqh7Wqk0fiOQMDNbPSGTuXztIP0SzA'

DB_PATH = f'supreme_db_{MASTER_ID}.json'

# --- [ كلاس إدارة الأجهزة (Device Emulator) ] ---
# هذا الكلاس يمنع طردك من الحساب عبر محاكاة أجهزة مختلفة
class DeviceEmulator:
    DEVICES = [
        {"model": "iPhone 15 Pro", "sys": "iOS 17.4", "app": "10.8.1"},
        {"model": "Samsung Galaxy S24 Ultra", "sys": "Android 14", "app": "10.5.0"},
        {"model": "Desktop", "sys": "Windows 11", "app": "4.15.2"},
        {"model": "iPad Pro", "sys": "iPadOS 17", "app": "10.3.0"}
    ]
    
    @staticmethod
    def get_random():
        return random.choice(DeviceEmulator.DEVICES)

# --- [ نظام إدارة البيانات الضخم ] ---
class SupremeDB:
    def __init__(self):
        self.data = self.load()

    def load(self):
        if not os.path.exists(DB_PATH):
            default = {
                "accounts": {},
                "settings": {
                    "target": "@t06bot",
                    "ref": "",
                    "delay": 45,
                    "stealth": True
                },
                "stats": {
                    "success": 0,
                    "failed": 0,
                    "banned": 0
                }
            }
            with open(DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(default, f, indent=4)
            return default
        return json.load(open(DB_PATH, 'r', encoding='utf-8'))

    def save(self):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

db = SupremeDB()

# --- [ كلاس التمويه وتغيير الهوية ] ---
class IdentityManager:
    F_NAMES = ["Sajad", "Ali", "Murtada", "Zain", "Othman", "Laila", "Noor", "Huda"]
    L_NAMES = ["Al-Iraqi", "Khafaji", "Al-Saadi", "Al-Taie", "Al-Hassani"]
    
    @staticmethod
    async def randomize(client):
        try:
            full_name = f"{random.choice(IdentityManager.F_NAMES)} {random.choice(IdentityGuard.LAST_NAMES)}"
            await client(functions.account.UpdateProfileRequest(first_name=full_name))
            # اختيار صورة عشوائية لو أردت (اختياري)
            logger.info(f"Identity spoofed to: {full_name}")
        except: pass

# --- [ محرك التخطي العملاق - Titan Bypass Engine ] ---
async def titan_bypass_v4(client, target, ref_link):
    """
    أقوى محرك تخطي تم بناؤه حتى الآن:
    يستطيع التعامل مع البوتات التي تتطلب أكثر من 15 قناة اشتراك.
    """
    try:
        current_bot = target
        # 1. تفعيل الإحالة
        if "start=" in ref_link:
            param = ref_link.split('start=')[-1]
            bot_user = ref_link.split('/')[-1].split('?')[0]
            await client(functions.messages.StartBotRequest(
                bot=bot_user, peer=bot_user, start_param=param
            ))
            current_bot = bot_user
            logger.info(f"Referral Start: {param}")

        # 2. حلقة التخطّي المتسلسلة (Deep Loop)
        for _ in range(20):
            await client.send_message(current_bot, "/start")
            await asyncio.sleep(7) # تأخير كافٍ لتجنب الـ Flood
            
            messages = await client.get_messages(current_bot, limit=1)
            if not messages or not messages[0].reply_markup:
                break # تم فتح البوت بنجاح
                
            msg = messages[0]
            action = False
            
            # فحص الأزرار الشفافة بحثاً عن روابط تليجرام
            for row in msg.reply_markup.rows:
                for btn in row.buttons:
                    if isinstance(btn, types.KeyboardButtonUrl):
                        url = btn.url
                        if "t.me/" in url:
                            action = True
                            try:
                                channel = url.split('/')[-1].replace('+', '')
                                if "joinchat" in url or "+" in url:
                                    try: await client(functions.messages.ImportChatInviteRequest(hash=channel))
                                    except: await client(functions.messages.CheckChatInviteRequest(hash=channel))
                                else:
                                    await client(JoinChannelRequest(channel=channel))
                                logger.info(f"Successfully joined: {channel}")
                            except: pass
            
            # إذا لم تكن هناك روابط، نبحث عن أزرار التأكيد
            if not action:
                for row in msg.reply_markup.rows:
                    for btn in row.buttons:
                        if any(txt in btn.text for txt in ["تحقق", "تم", "تأكيد", "Done", "Check"]):
                            await msg.click(text=btn.text)
                            await asyncio.sleep(3)
                            action = True
                if not action: break
                
    except Exception as e:
        logger.error(f"Titan Bypass encountered an issue: {e}")

# --- [ نظام إدارة الجلسات (Safe Session Handler) ] ---
# هذا القسم هو المسؤول عن عدم تسجيل خروجك
async def run_safe_session(phone, info):
    device = DeviceEmulator.get_random()
    client = TelegramClient(
        StringSession(info['ss']), API_ID, API_HASH,
        device_model=device['model'],
        system_version=device['sys'],
        app_version=device['app']
    )
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning(f"Account {phone} is unauthorized (Logged out or Banned).")
            return False
            
        # تنفيذ التمويه
        if db.data['settings']['stealth']:
            await IdentityManager.randomize(client)
            
        # تنفيذ التجميع والتخطي
        target = db.data['settings']['target']
        ref = db.data['settings']['ref']
        await titan_bypass_v4(client, target, ref)
        
        # محاولة أخيرة للضغط على زر التجميع
        await asyncio.sleep(5)
        msgs = await client.get_messages(target, limit=1)
        if msgs and msgs[0].reply_markup:
            for row in msgs[0].reply_markup.rows:
                for b in row.buttons:
                    if any(x in b.text for x in ["هدية", "يومية", "تجميع"]):
                        await msgs[0].click(text=b.text)
                        db.data['stats']['success'] += 1
                        db.save()
        
        await client.disconnect()
        return True
    except Exception as e:
        logger.error(f"Error in safe session: {e}")
        return False

# --- [ المحرك الرئيسي (Automation Core) ] ---
async def automation_loop():
    while True:
        logger.info("Starting a new farming cycle...")
        accounts = list(db.data['accounts'].items())
        
        for phone, info in accounts:
            success = await run_safe_session(phone, info)
            if not success:
                db.data['stats']['failed'] += 1
                db.save()
            
            wait = db.data['settings']['delay'] + random.randint(10, 30)
            logger.info(f"Waiting {wait}s before next account...")
            await asyncio.sleep(wait)
            
        logger.info("Cycle complete. Waiting 24 hours.")
        await asyncio.sleep(86400)

# --- [ واجهة التحكم - Imperial Control Center ] ---
manager = TelegramClient(f'supreme_bot_{MASTER_ID}', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@manager.on(events.NewMessage(pattern='/start'))
async def main_panel(event):
    if event.sender_id != MASTER_ID: return
    
    stats = db.data['stats']
    settings = db.data['settings']
    
    msg = (
        "👑 **مركز التحكم الإمبراطوري - الإصدار الأعلى** 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 الحسابات: `{len(db.data['accounts'])}` | 🎯 الهدف: `{settings['target']}`\n"
        f"🔗 الإحالة: `{settings['ref'][:20] if settings['ref'] else 'None'}...` \n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ نجاح: `{stats['success']}` | ❌ فشل: `{stats['failed']}`\n"
        f"🛡️ التمويه: `{'نشط' if settings['stealth'] else 'معطل'}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "إدارة المنظومة:"
    )
    
    btns = [
        [Button.inline("➕ إضافة حساب (String)", "add"), Button.inline("🗑️ حذف حساب", "del")],
        [Button.inline("🎯 البوت المستهدف", "st"), Button.inline("🔗 رابط الإحالة", "sr")],
        [Button.inline("⚙️ الإعدادات", "set"), Button.inline("📊 الحسابات", "list")],
        [Button.inline("📥 أداة الاستخراج", "tool"), Button.inline("🚀 بدء الآن", "run")],
        [Button.url("👨‍💻 المطور", "https://t.me/Tele_Sajad")]
    ]
    await event.reply(msg, buttons=btns)

@manager.on(events.CallbackQuery)
async def callback_router(event):
    if event.sender_id != MASTER_ID: return
    data = event.data.decode()
    
    if data == "add":
        async with manager.conversation(event.sender_id, timeout=300) as conv:
            await conv.send_message("🔑 **أرسل الـ String Session:**")
            ss = (await conv.get_response()).text.strip()
            await conv.send_message("📱 **أرسل الرقم (بدون +):**")
            ph = (await conv.get_response()).text.strip()
            
            load_msg = await conv.send_message("⏳ جاري فحص السيشن وتثبيت بيانات الجهاز...")
            try:
                # محاكاة جهاز حقيقي عند الفحص الأول
                dev = DeviceEmulator.get_random()
                temp = TelegramClient(StringSession(ss), API_ID, API_HASH, 
                                      device_model=dev['model'], system_version=dev['sys'])
                await temp.connect()
                if await temp.is_user_authorized():
                    me = await temp.get_me()
                    db.data['accounts'][me.phone] = {"ss": ss, "name": me.first_name, "device": dev}
                    db.save()
                    await load_msg.edit(f"✅ تم الربط بنجاح: {me.first_name}\n📱 الجهاز المحاكي: {dev['model']}")
                else:
                    await load_msg.edit("❌ السيشن غير صالح.")
                await temp.disconnect()
            except Exception as e: await load_msg.edit(f"⚠️ خطأ: {e}")

    elif data == "list":
        acc_list = "📋 **الحسابات المربوطة:**\n"
        for p, i in db.data['accounts'].items():
            acc_list += f"• `+{p}` - {i['name']} ({i.get('device', {}).get('model', 'Unknown')})\n"
        await event.respond(acc_list)

    elif data == "st":
        async with manager.conversation(event.sender_id) as conv:
            await conv.send_message("🎯 أرسل يوزر البوت المستهدف:")
            db.data['settings']['target'] = (await conv.get_response()).text.strip()
            db.save()
            await conv.send_message("✅ تم التحديث.")

    elif data == "sr":
        async with manager.conversation(event.sender_id) as conv:
            await conv.send_message("🔗 أرسل رابط الإحالة:")
            db.data['settings']['ref'] = (await conv.get_response()).text.strip()
            db.save()
            await conv.send_message("✅ تم الحفظ.")

    elif data == "tool":
        code = (f"from telethon import TelegramClient;import asyncio\n"
                f"async def m():\n"
                f" async with TelegramClient(None,{API_ID},'{API_HASH}') as c:print(c.session.save())\n"
                f"asyncio.run(m())")
        with open("extract.py", "w") as f: f.write(code)
        await event.respond("🛠 أداة الاستخراج الخاصة بك:", file="extract.py")

# --- [ الإطلاق النهائي ] ---
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(automation_loop())
    logger.info("🔥 SUPREME TITAN SYSTEM IS ONLINE.")
    manager.run_until_disconnected()
