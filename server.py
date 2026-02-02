# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE IMPERIAL SESSION FACTORY - ULTIMATE BYPASS V25.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
نظام متكامل يدعم:
1. روابط الإحالة (Referral) وحساب النقاط تلقائياً.
2. تخطي الاشتراك الإجباري عبر إرسال /start المتكرر.
3. إرسال طلبات الانضمام للقنوات الخاصة (Request Join).
4. فحص تطابق السيشن والرقم لضمان الأمان.
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
from telethon.errors import *

# --- [ إعدادات السجلات ] ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[logging.FileHandler("imperial_core.log"), logging.StreamHandler()]
)
logger = logging.getLogger("ImperialSystem")

# --- [ الثوابت ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

if len(sys.argv) > 2:
    BOT_TOKEN = sys.argv[1]
    MASTER_ID = int(sys.argv[2])
    SUB_MODE = True
else:
    MASTER_ID = 8504553407  
    BOT_TOKEN = '8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY'
    SUB_MODE = False

DB_ACCS = f'imp_accounts_{MASTER_ID}.json'

# --- [ نظام إدارة البيانات ] ---
class Database:
    @staticmethod
    def load():
        if not os.path.exists(DB_ACCS):
            with open(DB_ACCS, 'w', encoding='utf-8') as f:
                json.dump({"accounts": {}, "settings": {"target": "@t06bot", "invite_link": ""}}, f)
        return json.load(open(DB_ACCS, 'r', encoding='utf-8'))

    @staticmethod
    def save(data):
        with open(DB_ACCS, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

# --- [ محرك تخطي الاشتراك والإحالات الذكي ] ---

async def smart_referral_bypass(client, link, target_bot):
    """
    الدالة الجوهرية:
    1. تحليل الرابط (هل هو إحالة أم قناة؟).
    2. تنفيذ الإحالة أو الانضمام.
    3. تخطي الاشتراك الإجباري المتسلسل داخل البوت.
    """
    try:
        # --- الخطوة 1: معالجة رابط الإحالة ---
        if "start=" in link:
            # استخراج الكود مثل: 0005n78vig
            start_param = link.split('start=')[-1]
            # استخراج يوزر البوت من الرابط
            bot_user = link.split('/')[-1].split('?')[0]
            
            # إرسال طلب البدء الرسمي (Referral Start)
            await client(functions.messages.StartBotRequest(
                bot=bot_user,
                peer=bot_user,
                start_param=start_param
            ))
            logger.info(f"✅ تم إرسال الإحالة بالكود: {start_param}")
            target_bot = bot_user # تحديث الهدف ليكون البوت الذي في رابط الإحالة
        
        # --- الخطوة 2: الانضمام للقنوات (سواء كانت في الرابط أو اشتراك إجباري) ---
        elif "t.me/" in link:
            path = link.split('/')[-1]
            try:
                if path.startswith('+') or "joinchat" in link:
                    h = path.replace('+', '') if path.startswith('+') else link.split('/')[-1]
                    await client(functions.messages.ImportChatInviteRequest(hash=h))
                else:
                    await client(functions.channels.JoinChannelRequest(channel=path))
            except Exception:
                # إذا كانت قناة بطلب انضمام (Request)
                h = link.split('/')[-1].replace('+', '')
                await client(functions.messages.CheckChatInviteRequest(hash=h))

        # --- الخطوة 3: تخطي الاشتراك الإجباري المتسلسل داخل البوت ---
        for i in range(7): # محاولة تخطي حتى 7 قنوات إجبارية
            await client.send_message(target_bot, "/start")
            await asyncio.sleep(4)
            
            msgs = await client.get_messages(target_bot, limit=1)
            if not msgs or not msgs[0].reply_markup:
                break # البوت فتح ولا توجد أزرار اشتراك
                
            found_join_btn = False
            for row in msgs[0].reply_markup.rows:
                for btn in row.buttons:
                    if isinstance(btn, types.KeyboardButtonUrl):
                        # انضمام للقناة الموجودة في الزر
                        url = btn.url
                        found_join_btn = True
                        try:
                            if "t.me/+" in url or "joinchat" in url:
                                h = url.split('/')[-1].replace('+', '')
                                try: await client(functions.messages.ImportChatInviteRequest(hash=h))
                                except: await client(functions.messages.CheckChatInviteRequest(hash=h))
                            else:
                                await client(functions.channels.JoinChannelRequest(channel=url.split('/')[-1]))
                        except: pass
            
            if not found_join_btn:
                # إذا لم نجد روابط، ربما يوجد زر "تحقق"
                for row in msgs[0].reply_markup.rows:
                    for btn in row.buttons:
                        if any(x in btn.text for x in ["تحقق", "تم", "تاكيد"]):
                            await msgs[0].click(text=btn.text)
                            await asyncio.sleep(2)
                break
                
    except Exception as e:
        logger.error(f"Error in smart bypass: {e}")

# --- [ محرك الأتمتة الرئيسي ] ---

async def farming_cycle():
    while True:
        db_data = Database.load()
        accs = db_data.get("accounts", {})
        target = db_data["settings"].get("target", "@t06bot")
        invite = db_data["settings"].get("invite_link", "")
        
        for phone, info in accs.items():
            try:
                async with TelegramClient(StringSession(info['ss']), API_ID, API_HASH) as client:
                    # تنفيذ نظام الإحالة والتخطي
                    await smart_referral_bypass(client, invite if invite else target, target)
                    
                    # محاولة تجميع الهدية بعد التخطي
                    await asyncio.sleep(3)
                    msgs = await client.get_messages(target, limit=1)
                    if msgs and msgs[0].reply_markup:
                        for row in msgs[0].reply_markup.rows:
                            for b in row.buttons:
                                if any(w in b.text for w in ["هدية", "يومية", "تجميع"]):
                                    await msgs[0].click(text=b.text)
                await asyncio.sleep(random.randint(20, 50))
            except: continue
        await asyncio.sleep(86400)

# --- [ واجهة البوت ] ---

bot = TelegramClient(f'bot_{MASTER_ID}', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    if event.sender_id != MASTER_ID: return
    db = Database.load()
    msg = (
        "👑 **نظام المصنع الإمبراطوري المتكامل** 👑\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 الحسابات: `{len(db['accounts'])}`\n"
        f"🎯 البوت: `{db['settings']['target']}`\n"
        f"🔗 الرابط: `{db['settings']['invite_link'][:30] if db['settings']['invite_link'] else 'غير محدد'}...`"
    )
    btns = [
        [Button.inline("➕ ربط سيشن", "add"), Button.inline("🗑️ حذف حساب", "del")],
        [Button.inline("🎯 البوت المستهدف", "set_t"), Button.inline("🔗 رابط الإحالة", "set_i")],
        [Button.inline("📊 الحسابات", "list"), Button.inline("📥 أداة الاستخراج", "tool")]
    ]
    await event.reply(msg, buttons=btns)

@bot.on(events.CallbackQuery)
async def router(event):
    if event.sender_id != MASTER_ID: return
    data = event.data.decode()
    db = Database.load()

    if data == "set_t":
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message("🎯 **أرسل يوزر البوت المستهدف:**")
            db['settings']['target'] = (await conv.get_response()).text.strip()
            Database.save(db)
            await conv.send_message("✅ تم الحفظ.")

    elif data == "set_i":
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message("🔗 **أرسل رابط الإحالة (الذي يحتوي على ?start=):**")
            db['settings']['invite_link'] = (await conv.get_response()).text.strip()
            Database.save(db)
            await conv.send_message("✅ تم حفظ رابط الإحالة بنجاح.")

    elif data == "add":
        async with bot.conversation(event.sender_id, timeout=300) as conv:
            await conv.send_message("🔑 **أرسل السيشن (String Session):**")
            ss = (await conv.get_response()).text.strip()
            await conv.send_message("📱 **أرسل الرقم المرتبط للتأكيد (بدون +):**")
            ph = (await conv.get_response()).text.strip()
            
            try:
                temp = TelegramClient(StringSession(ss), API_ID, API_HASH)
                await temp.connect()
                me = await temp.get_me()
                if re.sub(r'\D', '', ph) in me.phone:
                    db['accounts'][me.phone] = {"ss": ss, "name": me.first_name}
                    Database.save(db)
                    await conv.send_message(f"✅ تم ربط الحساب: {me.first_name}")
                else:
                    await conv.send_message("❌ الرقم غير مطابق للسيشن!")
                await temp.disconnect()
            except Exception as e: await conv.send_message(f"⚠️ خطأ: {e}")

    elif data == "list":
        res = "📋 **قائمة الحسابات المربوطة:**\n"
        for p, i in db['accounts'].items():
            res += f"• `+{p}` - {i['name']}\n"
        await event.respond(res)

    elif data == "tool":
        sc = f"from telethon import TelegramClient;import asyncio;async def m():\n async with TelegramClient(None,{API_ID},'{API_HASH}') as c:print(c.session.save())\nasyncio.run(m())"
        with open("tool.py", "w") as f: f.write(sc)
        await event.respond("🛠 أداة الاستخراج:", file="tool.py")

# --- [ الإطلاق ] ---
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(farming_cycle())
    bot.run_until_disconnected()
