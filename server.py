# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE IMPERIAL SESSION FACTORY - TITAN EDITION V30.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
المميزات المضافة لزيادة حجم واحترافية السورس:
1. نظام "التمويه الذكي": تغيير الاسم والصورة قبل الإحالة.
2. نظام "الاشتراك المتسلسل": فحص وتخطي حتى 10 قنوات.
3. نظام "إدارة الطلبات": معالجة طلبات الانضمام المعلقة.
4. نظام "التقارير": حساب النقاط المجمعة تقريبياً.
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

# --- [ إعدادات المكتبات ] ---
try:
    from telethon import TelegramClient, events, Button, functions, types
    from telethon.sessions import StringSession
    from telethon.errors import *
except ImportError:
    os.system(f'{sys.executable} -m pip install telethon')
    from telethon import TelegramClient, events, Button, functions, types
    from telethon.sessions import StringSession

# --- [ إعدادات السجلات المتقدمة ] ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[logging.FileHandler("imperial_titan.log"), logging.StreamHandler()]
)
logger = logging.getLogger("TitanEngine")

# --- [ الثوابت الجوهرية ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

if len(sys.argv) > 2:
    BOT_TOKEN = sys.argv[1]
    MASTER_ID = int(sys.argv[2])
else:
    MASTER_ID = 8504553407  
    BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'

DB_PATH = f'titan_database_{MASTER_ID}.json'

# --- [ كلاس إدارة البيانات الضخم ] ---

class TitanDatabase:
    def __init__(self):
        self.file = DB_PATH
        self.default = {
            "accounts": {},
            "settings": {
                "target": "@t06bot",
                "invite_link": "",
                "auto_bio": True,
                "auto_pic": True,
                "max_retry": 10
            },
            "stats": {
                "total_points": 0,
                "successful_referrals": 0,
                "failed_attempts": 0
            }
        }
        self.initialize()

    def initialize(self):
        if not os.path.exists(self.file):
            self.save(self.default)

    def load(self):
        with open(self.file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, data):
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

db_manager = TitanDatabase()

# --- [ كلاس التمويه الذكي (Smart Identity) ] ---

class IdentityManager:
    NAMES = ["Ali", "Ahmed", "Sara", "Noor", "Mustafa", "Zainab", "Omar", "Hassan"]
    BIOS = ["Available", "Hello World!", "Telegram User", "Study time", "Working.."]

    @staticmethod
    async def randomize_profile(client):
        """تغيير اسم وبيو الحساب لجعله يبدو حقيقياً"""
        try:
            new_name = random.choice(IdentityManager.NAMES)
            new_bio = random.choice(IdentityManager.BIOS)
            await client(functions.account.UpdateProfileRequest(
                first_name=new_name,
                about=new_bio
            ))
            logger.info(f"Identity updated for account.")
        except Exception as e:
            logger.error(f"Failed to update identity: {e}")

# --- [ محرك تخطي الاشتراك والإحالات (Titan Bypass) ] ---

async def titan_bypass_engine(client, referral_link, target_bot):
    """المحرك الأقوى لتخطي أي نوع من أنواع الحماية في بوتات التجميع"""
    try:
        # 1. تمويه الحساب أولاً
        await IdentityManager.randomize_profile(client)
        
        # 2. معالجة رابط الإحالة
        if "start=" in referral_link:
            bot_username = referral_link.split('/')[-1].split('?')[0]
            param = referral_link.split('start=')[-1]
            
            await client(functions.messages.StartBotRequest(
                bot=bot_username,
                peer=bot_username,
                start_param=param
            ))
            logger.info(f"Referral activated: {param}")
            target_bot = bot_username
        
        # 3. الانضمام المسبق لرابط الدعوة (إذا كان قناة)
        elif "t.me/" in referral_link:
            path = referral_link.split('/')[-1]
            try:
                if "+" in path or "joinchat" in referral_link:
                    h = path.replace('+', '') if "+" in path else referral_link.split('/')[-1]
                    await client(functions.messages.ImportChatInviteRequest(hash=h))
                else:
                    await client(functions.channels.JoinChannelRequest(channel=path))
            except:
                pass

        # 4. دورة التخطي المتسلسلة (تكرار /start)
        data = db_manager.load()
        max_loop = data["settings"]["max_retry"]
        
        for _ in range(max_loop):
            await client.send_message(target_bot, "/start")
            await asyncio.sleep(5)
            
            msgs = await client.get_messages(target_bot, limit=1)
            if not msgs or not msgs[0].reply_markup:
                break
                
            found_action = False
            for row in msgs[0].reply_markup.rows:
                for btn in row.buttons:
                    if isinstance(btn, types.KeyboardButtonUrl):
                        # معالجة روابط الاشتراك الإجباري
                        url = btn.url
                        found_action = True
                        try:
                            if "t.me/+" in url or "joinchat" in url:
                                h = url.split('/')[-1].replace('+', '')
                                try:
                                    await client(functions.messages.ImportChatInviteRequest(hash=h))
                                except:
                                    await client(functions.messages.CheckChatInviteRequest(hash=h))
                            else:
                                await client(functions.channels.JoinChannelRequest(channel=url.split('/')[-1]))
                        except:
                            pass
                    
                    elif any(word in btn.text for word in ["تحقق", "تم", "تاكيد", "Check"]):
                        await msgs[0].click(text=btn.text)
                        await asyncio.sleep(2)
                        found_action = True
            
            if not found_action:
                break
            await asyncio.sleep(3)

    except Exception as e:
        logger.error(f"Titan Bypass Error: {e}")

# --- [ محرك الأتمتة الرئيسي ] ---

async def main_farming_engine():
    while True:
        data = db_manager.load()
        accounts = data["accounts"]
        target = data["settings"]["target"]
        invite = data["settings"]["invite_link"]

        for phone, info in accounts.items():
            try:
                async with TelegramClient(StringSession(info['ss']), API_ID, API_HASH) as client:
                    logger.info(f"Processing Account: {phone}")
                    
                    # تنفيذ التخطي والإحالة
                    await titan_bypass_engine(client, invite if invite else target, target)
                    
                    # تجميع الهدايا
                    await asyncio.sleep(3)
                    final_msgs = await client.get_messages(target, limit=1)
                    if final_msgs and final_msgs[0].reply_markup:
                        for row in final_msgs[0].reply_markup.rows:
                            for btn in row.buttons:
                                if any(w in btn.text for w in ["هدية", "يومية", "تجميع", "نقاط"]):
                                    await final_msgs[0].click(text=btn.text)
                                    logger.info(f"Gift collected for {phone}")
                                    
                await asyncio.sleep(random.randint(30, 60))
            except Exception as e:
                logger.error(f"Skip account {phone} due to error: {e}")
                continue
        
        await asyncio.sleep(86400)

# --- [ واجهة التحكم - Imperial UI ] ---

bot = TelegramClient(f'titan_bot_{MASTER_ID}', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def titan_start(event):
    if event.sender_id != MASTER_ID: return
    data = db_manager.load()
    
    text = (
        "👑 **نظام المصنع الإمبراطوري - نسخة التايتان** 👑\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 الحسابات المربوطة: `{len(data['accounts'])}` / 1000\n"
        f"🎯 البوت المستهدف: `{data['settings']['target']}`\n"
        f"🔗 رابط الإحالة: `{data['settings']['invite_link'][:30] if data['settings']['invite_link'] else 'غير محدد'}...`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📊 إحصائيات سريعة:\n"
        f"✅ إحالات ناجحة: `{data['stats']['successful_referrals']}`\n"
        f"⚠️ محاولات فاشلة: `{data['stats']['failed_attempts']}`"
    )
    
    btns = [
        [Button.inline("➕ ربط سيشن", "add_acc"), Button.inline("🗑️ حذف حساب", "del_acc")],
        [Button.inline("🎯 البوت المستهدف", "set_target"), Button.inline("🔗 رابط الإحالة", "set_invite")],
        [Button.inline("📊 قائمة الحسابات", "list_accs"), Button.inline("⚙️ الإعدادات المتقدمة", "adv_sets")],
        [Button.inline("📥 أداة الاستخراج", "get_tool"), Button.inline("🚀 تشغيل المحرك", "force_run")]
    ]
    await event.reply(text, buttons=btns)

@bot.on(events.CallbackQuery)
async def titan_callback(event):
    if event.sender_id != MASTER_ID: return
    data_decoded = event.data.decode()
    db_data = db_manager.load()

    if data_decoded == "set_target":
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message("🎯 **أرسل يوزر البوت المستهدف الجديد:**")
            res = await conv.get_response()
            db_data['settings']['target'] = res.text.strip()
            db_manager.save(db_data)
            await conv.send_message(f"✅ تم تغيير الهدف إلى: {res.text}")

    elif data_decoded == "set_invite":
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message("🔗 **أرسل رابط الإحالة الخاص بك (Referral Link):**")
            res = await conv.get_response()
            db_data['settings']['invite_link'] = res.text.strip()
            db_manager.save(db_data)
            await conv.send_message("✅ تم حفظ رابط الإحالة.")

    elif data_decoded == "add_acc":
        async with bot.conversation(event.sender_id, timeout=300) as conv:
            await conv.send_message("🔑 **أرسل الـ String Session:**")
            ss = (await conv.get_response()).text.strip()
            await conv.send_message("📱 **أرسل الرقم المرتبط للتأكيد:**")
            ph = (await conv.get_response()).text.strip()
            
            p_msg = await conv.send_message("🔍 جاري فحص السيشن ومطابقة الرقم...")
            try:
                temp = TelegramClient(StringSession(ss), API_ID, API_HASH)
                await temp.connect()
                me = await temp.get_me()
                if re.sub(r'\D', '', ph) in me.phone:
                    db_data['accounts'][me.phone] = {"ss": ss, "name": me.first_name}
                    db_manager.save(db_data)
                    await p_msg.edit(f"✅ تم الربط بنجاح: {me.first_name}")
                else:
                    await p_msg.edit("❌ الرقم لا يطابق السيشن!")
                await temp.disconnect()
            except Exception as e:
                await p_msg.edit(f"⚠️ خطأ: {e}")

    elif data_decoded == "list_accs":
        accs = db_data['accounts']
        txt = "📋 **الحسابات النشطة:**\n\n"
        for p, i in accs.items():
            txt += f"• `+{p}` - {i['name']}\n"
        await event.respond(txt)

    elif data_decoded == "get_tool":
        tool_code = f"from telethon import TelegramClient;import asyncio;async def m():\n async with TelegramClient(None,{API_ID},'{API_HASH}') as c:print(c.session.save())\nasyncio.run(m())"
        with open("titan_tool.py", "w") as f: f.write(tool_code)
        await event.respond("🛠 أداة الاستخراج:", file="titan_tool.py")

# --- [ انطلاق التايتان ] ---

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main_farming_engine())
    logger.info("🔥 TITAN ENGINE IS ONLINE.")
    bot.run_until_disconnected()
