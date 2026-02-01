# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE IMPERIAL SESSION FACTORY - V10.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
نظام متكامل لإدارة الحسابات، التجميع التلقائي، وفحص السيشنات
يتوافق مع أحدث إصدارات Telethon ويحتوي على نظام حماية متطور.
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
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError,
    PasswordHashInvalidError, PhoneNumberInvalidError,
    FloodWaitError, UserDeactivatedError, PeerIdInvalidError
)

# --- [ إعدادات السجلات - Advanced Logging ] ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s',
    handlers=[logging.FileHandler("system_core.log"), logging.StreamHandler()]
)
logger = logging.getLogger("ImperialFactory")

# --- [ الثوابت - Global Configuration ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

if len(sys.argv) > 2:
    BOT_TOKEN = sys.argv[1]
    MASTER_ID = int(sys.argv[2])
    SUB_MODE = True
else:
    MASTER_ID = 8504553407  
    BOT_TOKEN = '8331141429:AAGeDiqh7Wqk0fiOQMDNbPSGTuXztIP0SzA'
    SUB_MODE = False

DB_ACCS = f'imp_accounts_{MASTER_ID}.json'
DB_CONF = f'imp_config_{MASTER_ID}.json'

# --- [ كلاس إدارة الجلسات - Session Logic Class ] ---

class SessionManager:
    """كلاس احترافي للتعامل مع كل ما يخص سيشنات التيليجرام"""
    
    @staticmethod
    async def check_validity(ss_string):
        """فحص هل السيشن لا يزال يعمل أم انتهى"""
        client = TelegramClient(StringSession(ss_string), API_ID, API_HASH)
        try:
            await client.connect()
            is_auth = await client.is_user_authorized()
            return is_auth
        except Exception as e:
            logger.error(f"Error checking session: {e}")
            return False
        finally:
            await client.disconnect()

    @staticmethod
    async def get_account_info(ss_string):
        """جلب معلومات الحساب الكاملة"""
        client = TelegramClient(StringSession(ss_string), API_ID, API_HASH)
        try:
            await client.connect()
            me = await client.get_me()
            return me
        except Exception:
            return None
        finally:
            await client.disconnect()

# --- [ نظام إدارة البيانات - Persistent Storage ] ---

class Database:
    def __init__(self):
        self.setup_files()

    def setup_files(self):
        for f in [DB_ACCS, DB_CONF]:
            if not os.path.exists(f):
                with open(f, 'w', encoding='utf-8') as file:
                    json.dump({"accounts": {}, "settings": {"target": "@t06bot", "limit": 500}}, file)

    def get_all_accounts(self):
        with open(DB_ACCS, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("accounts", {})

    def add_account(self, phone, ss, name):
        data = self.get_full_data()
        data["accounts"][str(phone)] = {
            "ss": ss,
            "name": name,
            "status": "Active",
            "added_on": str(datetime.datetime.now())
        }
        self.save_full_data(data)

    def remove_account(self, phone):
        data = self.get_full_data()
        if str(phone) in data["accounts"]:
            del data["accounts"][str(phone)]
            self.save_full_data(data)
            return True
        return False

    def get_full_data(self):
        with open(DB_ACCS, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_full_data(self, data):
        with open(DB_ACCS, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

db = Database()

# --- [ محرك الأتمتة - Automation Engine ] ---

async def farming_cycle():
    """المحرك المسؤول عن تجميع الهدايا والنقاط تلقائياً"""
    while True:
        logger.info("Starting new farming cycle...")
        accounts = db.get_all_accounts()
        full_data = db.get_full_data()
        target = full_data["settings"].get("target", "@t06bot")
        
        for phone, info in accounts.items():
            try:
                async with TelegramClient(StringSession(info['ss']), API_ID, API_HASH) as client:
                    # إرسال ستارت للبوت
                    await client.send_message(target, "/start")
                    await asyncio.sleep(random.randint(5, 10))
                    
                    # تحليل الرسائل والضغط على الأزرار
                    messages = await client.get_messages(target, limit=1)
                    if messages and messages[0].reply_markup:
                        for row in messages[0].reply_markup.rows:
                            for btn in row.buttons:
                                if any(word in btn.text for word in ["هدية", "يومية", "كسب"]):
                                    await messages[0].click(text=btn.text)
                                    logger.info(f"Collected for: {phone}")
                
                # فاصل زمني بين حساب وآخر لتجنب الحظر
                await asyncio.sleep(random.randint(20, 40))
            except Exception as e:
                logger.warning(f"Failed for {phone}: {e}")
                continue
        
        # الانتظار 24 ساعة للدورة القادمة
        await asyncio.sleep(86400)

# --- [ واجهة البوت - Telegram Interface ] ---

bot = TelegramClient(f'imperial_bot_{MASTER_ID}', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    if event.sender_id != MASTER_ID: return
    
    accs = db.get_all_accounts()
    full_data = db.get_full_data()
    
    msg = (
        "👑 **نظام المصنع الإمبراطوري المتكامل** 👑\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 المطور: `{MASTER_ID}`\n"
        f"📱 الحسابات المربوطة: `{len(accs)}` / `{full_data['settings']['limit']}`\n"
        f"⚙️ الهدف الحالي: `{full_data['settings']['target']}`\n"
        f"🛡️ حالة النظام: `مستقر (Active)`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "اختر من القائمة أدناه لإدارة عملياتك:"
    )
    
    btns = [
        [Button.inline("➕ ربط سيشن جديد", "nav_add"), Button.inline("📥 أداة الاستخراج", "nav_tool")],
        [Button.inline("📊 عرض الحسابات", "nav_list"), Button.inline("⚙️ الإعدادات", "nav_set")],
        [Button.inline("🔍 فحص الصلاحية", "nav_check"), Button.inline("🗑️ مسح حساب", "nav_del")],
        [Button.inline("🚀 بدء تجميع يدوي", "nav_run"), Button.inline("📝 سجل العمليات", "nav_logs")],
        [Button.url("👨‍💻 المطور", "https://t.me/Tele_Sajad")]
    ]
    
    if not SUB_MODE:
        btns.insert(4, [Button.inline("💎 تنصيب نسخة لزبون", "nav_deploy")])
        
    await event.reply(msg, buttons=btns)

# --- [ معالجة الأزرار والمنطق - Callback Logic ] ---

@bot.on(events.CallbackQuery)
async def callback_router(event):
    if event.sender_id != MASTER_ID: return
    data = event.data.decode('utf-8')
    
    # --- التنقل بين القوائم ---
    if data == "nav_add":
        await handle_add_session(event)
    elif data == "nav_list":
        await handle_list_accounts(event)
    elif data == "nav_set":
        await handle_settings_menu(event)
    elif data == "nav_check":
        await handle_bulk_check(event)
    elif data == "nav_tool":
        await handle_send_tool(event)
    elif data == "nav_del":
        await handle_delete_process(event)
    elif data == "back_home":
        await start_cmd(event)

# --- [ دالة الربط والتحقق المعقدة ] ---

async def handle_add_session(event):
    async with bot.conversation(event.sender_id, timeout=300) as conv:
        try:
            await conv.send_message("💠 **يرجى إرسال الـ String Session الآن:**")
            ss_input = (await conv.get_response()).text.strip()
            
            await conv.send_message("📞 **أرسل رقم الهاتف المرتبط (بدون +):**")
            ph_input = (await conv.get_response()).text.strip()
            
            wait_msg = await conv.send_message("⏳ جاري التحقق من صحة السيشن ومطابقة الرقم...")
            
            # التحقق العميق
            client = TelegramClient(StringSession(ss_input), API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.disconnect()
                return await wait_msg.edit("❌ **فشل:** السيشن منتهي الصلاحية أو تم تسجيل الخروج منه.")
                
            me = await client.get_me()
            clean_in = re.sub(r'\D', '', ph_input)
            clean_me = re.sub(r'\D', '', me.phone)
            
            if clean_in not in clean_me:
                await client.disconnect()
                return await wait_msg.edit(f"❌ **خطأ تطابق:** الرقم المدخل لا ينتمي لهذا السيشن! السيشن يخص: `+{clean_me}`")
            
            # حفظ في القاعدة
            db.add_account(clean_me, ss_input, me.first_name)
            await client.disconnect()
            
            await wait_msg.edit(f"✅ **تم الربط بنجاح!**\n👤 الاسم: `{me.first_name}`\n📱 الرقم: `+{clean_me}`")
            
        except Exception as e:
            await event.respond(f"⚠️ خطأ غير متوقع: {e}")

# --- [ قائمة الإعدادات المتقدمة ] ---

async def handle_settings_menu(event):
    full_data = db.get_full_data()
    target = full_data["settings"]["target"]
    limit = full_data["settings"]["limit"]
    
    txt = (
        "⚙️ **لوحة التحكم بالإعدادات الفنية**\n\n"
        f"🎯 البوت المستهدف: `{target}`\n"
        f"📏 الحد الأقصى للحسابات: `{limit}`\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    btns = [
        [Button.inline("🎯 تغيير البوت المستهدف", "set_target")],
        [Button.inline("📏 تعديل حد الحسابات", "set_limit")],
        [Button.inline("⬅️ رجوع للمنيو", "back_home")]
    ]
    await event.edit(txt, buttons=btns)

# --- [ أداة الاستخراج - Advanced Version ] ---

async def handle_send_tool(event):
    tool_code = f"""
import os, asyncio, platform
try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except:
    os.system('pip install telethon')
    from telethon import TelegramClient
    from telethon.sessions import StringSession

API_ID = {API_ID}
API_HASH = '{API_HASH}'

async def main():
    os.system('cls' if platform.system() == 'Windows' else 'clear')
    print("====================================")
    print("      IMPERIAL EXTRACTOR TOOL")
    print("====================================")
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\\nYour Session String is:\\n")
        print(client.session.save())
        print("\\nCopy it and send it to your bot.")
        input("\\nPress Enter to exit...")

if __name__ == '__main__':
    asyncio.run(main())
"""
    with open("extractor.py", "w", encoding='utf-8') as f:
        f.write(tool_code)
    await event.respond("🛠️ **أداة استخراج السيشن الخاصة بك:**", file="extractor.py")
    os.remove("extractor.py")

# --- [ وظائف إضافية لتكملة السورس ] ---

async def handle_list_accounts(event):
    accs = db.get_all_accounts()
    if not accs: return await event.answer("⚠️ لا توجد حسابات مضافة.", alert=True)
    
    out = "📊 **قائمة حساباتك المسجلة:**\n\n"
    for p, i in accs.items():
        out += f"• `+{p}` | {i['name']} | ✅\n"
    
    await event.respond(out, buttons=[Button.inline("⬅️ رجوع", "back_home")])

async def handle_bulk_check(event):
    await event.answer("🔄 جاري فحص جميع الحسابات، يرجى الانتظار...", alert=False)
    accs = db.get_all_accounts()
    dead = 0
    for p, i in accs.items():
        if not await SessionManager.check_validity(i['ss']):
            dead += 1
    await event.respond(f"🔎 **نتائج الفحص:**\n✅ شغال: `{len(accs) - dead}`\n❌ متوقف: `{dead}`")

# --- [ إقلاع المنظومة ] ---

if __name__ == '__main__':
    # تشغيل المهام الخلفية
    loop = asyncio.get_event_loop()
    loop.create_task(farming_cycle())
    
    logger.info("🔥 The Imperial Factory is now ONLINE.")
    bot.run_until_disconnected()
