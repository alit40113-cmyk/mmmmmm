# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE IMPERIAL TITAN FACTORY - SUPREME CORRECTED EDITION 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- المطور الرئيسي: 8504553407
- الإصدار: 11.0 (Fixed Syntax)
- عدد الأسطر: +500
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import json
import asyncio
import datetime
import logging
import random
import time
import re
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import *

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [1] الإعدادات الأساسية والهوية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
BOT_TOKEN = "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY" 
MASTER_ID = 8504553407
DATABASE_NAME = "imperial_titan_final.json"

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('system_core.log'), logging.StreamHandler()]
)
logger = logging.getLogger("ImperialTitan")

# إنشاء المسارات
for path in ["sessions", "instances", "logs"]:
    if not os.path.exists(path):
        os.makedirs(path)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [2] محرك قاعدة البيانات (Core DB Manager)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CoreDB:
    def __init__(self, db_file):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        if not os.path.exists(self.db_file):
            initial = {
                "config": {
                    "master_id": MASTER_ID,
                    "target_bot": "@t06bot",
                    "ref_link": "",
                    "delay": 45
                },
                "master_accs": {},
                "clients": {},
                "history": []
            }
            self.save(initial)

    def load(self):
        with open(self.db_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, data):
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_history(self, action):
        data = self.load()
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        data['history'].append(f"[{dt}] {action}")
        if len(data['history']) > 50:
            data['history'].pop(0)
        self.save(data)

db = CoreDB(DATABASE_NAME)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [3] محرك التجميع والعمليات الذكية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class FarmCore:
    @staticmethod
    async def join_channels(client, message):
        """محرك تخطي قنوات الاشتراك الإجباري"""
        if not message.reply_markup:
            return
        for row in message.reply_markup.rows:
            for btn in row.buttons:
                if isinstance(btn, types.KeyboardButtonUrl):
                    try:
                        channel = btn.url.split('/')[-1]
                        await client(functions.channels.JoinChannelRequest(channel=channel))
                    except: pass

    @staticmethod
    async def process_ref(client, ref_link):
        try:
            bot_u = ref_link.split("/")[-1].split("?")[0]
            param = ref_link.split("start=")[-1]
            await client(functions.messages.StartBotRequest(bot=bot_u, peer=bot_u, start_param=param))
            return True
        except: return False

    @staticmethod
    async def process_gift(client, target):
        try:
            await client.send_message(target, "/start")
            await asyncio.sleep(4)
            for _ in range(5):
                msgs = await client.get_messages(target, limit=1)
                if not msgs or not msgs[0].reply_markup: break
                
                await FarmCore.join_channels(client, msgs[0])
                
                for row in msgs[0].reply_markup.rows:
                    for btn in row.buttons:
                        if any(x in btn.text for x in ["تحقق", "تم", "تأكيد", "Verify"]):
                            await msgs[0].click(text=btn.text)
                            await asyncio.sleep(3)
                        elif any(x in btn.text for x in ["هدية", "يومية", "Daily", "Gift"]):
                            await msgs[0].click(text=btn.text)
                            return True
            return False
        except: return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [4] محرك إدارة بوتات الزبائن (Sub-Bot Factory)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def run_sub_bot(c_id, c_token):
    try:
        sub = TelegramClient(f"instances/bot_{c_id}", API_ID, API_HASH)
        await sub.start(bot_token=c_token)
        
        @sub.on(events.NewMessage(pattern='/start'))
        async def sub_handler(event):
            if event.sender_id != int(c_id): return
            data = db.load()
            info = data['clients'].get(str(c_id))
            if not info: return
            
            exp = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
            if datetime.datetime.now() > exp:
                return await event.reply("⚠️ انتهى ترخيصك، تواصل مع المطور.")

            text = (f"🛡️ **لوحة التحكم الملكية**\n"
                    f"🔢 الحسابات: `{len(info['accs'])} / {info['limit']}`\n"
                    f"⏳ الانتهاء: `{info['expiry']}`")
            btns = [
                [Button.inline("➕ إضافة حساب", "c_add"), Button.inline("🗑️ مسح حساب", "c_del")],
                [Button.inline("🚀 بدء تجميع", "c_run")],
                [Button.inline("📊 عرض أرقامي", "c_list")]
            ]
            await event.reply(text, buttons=btns)

        @sub.on(events.CallbackQuery)
        async def sub_callback(event):
            cid = str(event.sender_id)
            data = db.load()
            query = event.data.decode()

            if query == "c_add":
                if len(data['clients'][cid]['accs']) >= data['clients'][cid]['limit']:
                    return await event.answer("❌ الحد ممتلئ!", alert=True)
                async with sub.conversation(event.sender_id) as conv:
                    await conv.send_message("🔑 أرسل الـ String Session:"); ss = (await conv.get_response()).text.strip()
                    await conv.send_message("📱 أرسل رقم الهاتف:"); ph = (await conv.get_response()).text.strip()
                    data['clients'][cid]['accs'][ph] = ss; db.save(data)
                    await conv.send_message("✅ تم الحفظ.")

            elif query == "c_del":
                async with sub.conversation(event.sender_id) as conv:
                    await conv.send_message("🗑️ أرسل الرقم للحذف:"); ph = (await conv.get_response()).text.strip()
                    if ph in data['clients'][cid]['accs']:
                        del data['clients'][cid]['accs'][ph]; db.save(data); await conv.send_message("✅ تم.")
            
            elif query == "c_list":
                accs = data['clients'][cid]['accs']
                m = "📊 أرقامك:\n" + "\n".join([f"📱 `{p}`" for p in accs]) if accs else "فارغة."
                await event.respond(m)

            elif query == "c_run":
                await event.answer("🚀 بدأ التجميع...", alert=False)
                for ph, ss in data['clients'][cid]['accs'].items():
                    try:
                        cl = TelegramClient(StringSession(ss), API_ID, API_HASH)
                        await cl.connect()
                        await FarmCore.process_ref(cl, data['config']['ref_link'])
                        await FarmCore.process_gift(cl, data['config']['target_bot'])
                        await cl.disconnect(); await asyncio.sleep(2)
                    except: continue
                await event.respond("🏁 انتهى التجميع.")

        await sub.run_until_disconnected()
    except: pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [5] بوت الماستر الرئيسي (The Imperial Master)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

master_bot = TelegramClient("Imperial_Core", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@master_bot.on(events.NewMessage(pattern='/start'))
async def master_ui(event):
    if event.sender_id != MASTER_ID: return
    data = db.load()
    dashboard = (
        f"👑 **مصنع الإمبراطورية العظيم**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 حسابات الماستر: `{len(data['master_accs'])}` \n"
        f"💎 الزبائن: `{len(data['clients'])}` \n"
        f"🎯 الهدف: `{data['config']['target_bot']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    btns = [
        [Button.inline("➕ إضافة حساب ماستر", "m_add"), Button.inline("🗑️ مسح حساب ماستر", "m_del")],
        [Button.inline("📊 حساباتي", "m_list"), Button.inline("🔍 فحص الصلاحية", "m_check")],
        [Button.inline("🚀 تجميع الماستر", "m_farm"), Button.inline("⚙️ الإعدادات", "m_set")],
        [Button.inline("💎 تنصيب لزبون", "m_deploy"), Button.inline("📝 السجلات", "m_logs")],
        [Button.inline("📩 الاستخراج", "m_tool"), Button.inline("🔄 ريستارت", "m_reboot")]
    ]
    await event.reply(dashboard, buttons=btns)

@master_bot.on(events.CallbackQuery)
async def master_logic(event):
    if event.sender_id != MASTER_ID: return
    data = db.load(); query = event.data.decode()

    # الإصلاح هنا: تم استبدال السطر الذي تسبب في الخطأ
    if query == "m_check":
        await event.answer("🔍 فحص الحسابات...", alert=False)
        live, dead = 0, 0
        accs_copy = data['master_accs'].copy()
        for ph, ss in accs_copy.items():
            try:
                c = TelegramClient(StringSession(ss), API_ID, API_HASH)
                await c.connect()
                if await c.is_user_authorized():
                    live += 1
                else:
                    dead += 1
                    data['master_accs'].pop(ph)
                await c.disconnect()
            except:
                dead += 1
                data['master_accs'].pop(ph)
        db.save(data)
        await event.respond(f"✅ النتيجة:\n🟢 فعال: {live}\n🔴 معطل: {dead}")

    elif query == "m_deploy":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("👤 أرسل ID الزبون:"); cid = (await conv.get_response()).text.strip()
            if not cid.isdigit(): return await conv.send_message("❌ ID غير صالح.")
            
            await conv.send_message("🔑 أرسل التوكن:"); ctok = (await conv.get_response()).text.strip()
            
            await conv.send_message("🔍 جاري التحقق من التوكن..."); 
            try:
                test = TelegramClient(f"temp_{cid}", API_ID, API_HASH)
                await test.start(bot_token=ctok); me = await test.get_me(); await test.disconnect()
                
                await conv.send_message("⏳ عدد الأيام:"); cdays = (await conv.get_response()).text.strip()
                await conv.send_message("🔢 حد الحسابات:"); clim = (await conv.get_response()).text.strip()
                
                exp = (datetime.datetime.now() + datetime.timedelta(days=int(cdays))).strftime('%Y-%m-%d')
                data['clients'][cid] = {"token": ctok, "expiry": exp, "limit": int(clim), "accs": {}}
                db.save(data); db.add_history(f"تم تفعيل زبون: {cid}")
                
                asyncio.create_task(run_sub_bot(cid, ctok))
                await conv.send_message(f"✅ تم بنجاح!\n🤖 البوت: @{me.username}")
            except: await conv.send_message("❌ التوكن غير صالح.")

    elif query == "m_add":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🔑 ارسل السيشن:"); ss = (await conv.get_response()).text.strip()
            await conv.send_message("📱 ارسل الرقم:"); ph = (await conv.get_response()).text.strip()
            data['master_accs'][ph] = ss; db.save(data); await conv.send_message("✅ تم الحفظ.")

    elif query == "m_del":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🗑️ ارسل الرقم:"); ph = (await conv.get_response()).text.strip()
            if ph in data['master_accs']:
                del data['master_accs'][ph]; db.save(data); await conv.send_message("✅ تم الحذف.")

    elif query == "m_list":
        m = "📊 حساباتك:\n" + "\n".join([f"📱 `{p}`" for p in data['master_accs']]) if data['master_accs'] else "لا يوجد"
        await event.respond(m)

    elif query == "m_farm":
        await event.answer("🚀 بدأ التجميع...", alert=True)
        for ph, ss in data['master_accs'].items():
            try:
                cl = TelegramClient(StringSession(ss), API_ID, API_HASH)
                await cl.connect()
                await FarmCore.process_ref(cl, data['config']['ref_link'])
                await FarmCore.process_gift(cl, data['config']['target_bot'])
                await cl.disconnect(); await asyncio.sleep(data['config']['delay'])
            except: continue
        await event.respond("🏁 انتهى تجميع الماستر.")

    elif query == "m_set":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🎯 يوزر الهدف:"); data['config']['target_bot'] = (await conv.get_response()).text.strip()
            await conv.send_message("🔗 رابط الإحالة:"); data['config']['ref_link'] = (await conv.get_response()).text.strip()
            await conv.send_message("⏳ وقت التأخير:"); data['config']['delay'] = int((await conv.get_response()).text.strip())
            db.save(data); await conv.send_message("✅ تم التحديث.")

    elif query == "m_logs":
        await event.respond("📝 سجل العمليات:\n\n" + "\n".join(data['history']))

    elif query == "m_tool":
        code = f"from telethon import TelegramClient\nimport asyncio\nasync def x():\n async with TelegramClient(None, {API_ID}, '{API_HASH}') as c: print(c.session.save())\nasyncio.run(x())"
        with open("GetSession.py", "w") as f: f.write(code)
        await event.respond("🛠 استخراج السيشن:", file="GetSession.py")

    elif query == "m_reboot":
        await event.answer("🔄 إعادة تشغيل...", alert=True)
        os.execl(sys.executable, sys.executable, *sys.argv)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [6] الإقلاع الذاتي عند بدء السيرفر
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def startup():
    data = db.load()
    logger.info(f"System Starting... Found {len(data['clients'])} instances.")
    for cid, info in data['clients'].items():
        exp = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
        if datetime.datetime.now() < exp:
            asyncio.create_task(run_sub_bot(cid, info['token']))
    logger.info("👑 System Online!")

if __name__ == "__main__":
    master_bot.loop.run_until_complete(startup())
    master_bot.run_until_disconnected()
