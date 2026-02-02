# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE IMPERIAL TITAN - VERSION 4.0 (ULTRA REPAIR) 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- المطور: 8504553407
- الحالة: نسخة إصلاح محرك تشغيل الزبائن
- الوظيفة: مصنع بوتات متكامل مع فحص توكنات عميق
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os, sys, json, asyncio, datetime, logging, re, time
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import *

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [1] الإعدادات الأساسية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
BOT_TOKEN = "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY" 
MASTER_ID = 8504553407
DB_PATH = "imperial_titan_v4.json"

# إعداد السجلات
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("TitanCore")

# تأكد من وجود المجلدات المطلوبة
for folder in ["sessions", "logs", "instances"]:
    if not os.path.exists(folder): os.makedirs(folder)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [2] محرك قاعدة البيانات المتطور
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TitanDB:
    @staticmethod
    def load():
        if not os.path.exists(DB_PATH):
            data = {
                "settings": {"target": "@t06bot", "ref": "", "delay": 40},
                "master_accs": {},
                "clients": {}, # {id: {token, expiry, limit, accs: {}}}
                "logs": []
            }
            TitanDB.save(data)
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save(data):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def add_log(text):
        db = TitanDB.load()
        db['logs'].append(f"[{datetime.datetime.now().strftime('%H:%M')}] {text}")
        if len(db['logs']) > 30: db['logs'].pop(0)
        TitanDB.save(db)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [3] كلاس تشغيل البوتات المستقلة (The Runner)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ClientBotRunner:
    """هذا الكلاس هو المسؤول عن نهوض بوت الزبون وضمان عدم توقفه"""
    
    active_instances = {}

    @staticmethod
    async def start_instance(c_id, c_token):
        if c_id in ClientBotRunner.active_instances:
            try: await ClientBotRunner.active_instances[c_id].disconnect()
            except: pass

        try:
            logger.info(f"🚀 Starting Client Bot: {c_id}")
            client = TelegramClient(f"instances/bot_{c_id}", API_ID, API_HASH)
            await client.start(bot_token=c_token)
            
            # حفظ الكلاينت في القائمة النشطة
            ClientBotRunner.active_instances[c_id] = client

            @client.on(events.NewMessage(pattern='/start'))
            async def sub_start(event):
                if event.sender_id != int(c_id): return
                db = TitanDB.load()
                info = db['clients'].get(str(c_id))
                if not info: return
                
                exp = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
                if datetime.datetime.now() > exp:
                    return await event.reply("⚠️ انتهى ترخيصك، تواصل مع المطور.")

                btns = [
                    [Button.inline("➕ إضافة حساب", "c_add"), Button.inline("🗑️ مسح حساب", "c_del")],
                    [Button.inline("🚀 تجميع شامل", "c_farm")],
                    [Button.inline("📊 حساباتي", "c_list")]
                ]
                await event.reply(f"💎 **لوحة الزبون الملكية**\n🔢 الحسابات: `{len(info['accs'])}/{info['limit']}`\n⏳ الانتهاء: `{info['expiry']}`", buttons=btns)

            @client.on(events.CallbackQuery)
            async def sub_logic(event):
                cid = str(event.sender_id)
                db = TitanDB.load()
                cmd = event.data.decode()

                if cmd == "c_add":
                    if len(db['clients'][cid]['accs']) >= db['clients'][cid]['limit']:
                        return await event.answer("❌ الحد ممتلئ!", alert=True)
                    async with client.conversation(event.sender_id) as conv:
                        await conv.send_message("🔑 أرسل الـ String Session:"); ss = (await conv.get_response()).text.strip()
                        await conv.send_message("📱 أرسل الرقم:"); ph = (await conv.get_response()).text.strip()
                        db['clients'][cid]['accs'][ph] = ss; TitanDB.save(db)
                        await conv.send_message("✅ تم الحفظ.")

                elif cmd == "c_del":
                    async with client.conversation(event.sender_id) as conv:
                        await conv.send_message("🗑️ أرسل الرقم لحذفه:"); ph = (await conv.get_response()).text.strip()
                        if ph in db['clients'][cid]['accs']:
                            del db['clients'][cid]['accs'][ph]; TitanDB.save(db)
                            await conv.send_message("✅ تم الحذف.")
                
                elif cmd == "c_list":
                    accs = db['clients'][cid]['accs']
                    m = "📊 أرقامك:\n" + "\n".join([f"📱 `{p}`" for p in accs]) if accs else "فارغة"
                    await event.respond(m)

                elif cmd == "c_farm":
                    await event.answer("🚀 بدأ التجميع...", alert=False)
                    for ph, ss in db['clients'][cid]['accs'].items():
                        # محرك التجميع المصغر داخل بوت الزبون
                        try:
                            t_cl = TelegramClient(StringSession(ss), API_ID, API_HASH)
                            await t_cl.connect()
                            # تنفيذ الإحالة
                            if db['settings']['ref']:
                                u = db['settings']['ref'].split("/")[-1].split("?")[0]
                                p = db['settings']['ref'].split("start=")[-1]
                                await t_cl(functions.messages.StartBotRequest(bot=u, peer=u, start_param=p))
                            # تنفيذ الهدية
                            await t_cl.send_message(db['settings']['target'], "/start")
                            await t_cl.disconnect()
                        except: pass
                    await event.respond("🏁 انتهى التجميع.")

            logger.info(f"✅ Bot {c_id} is now fully operational.")
            await client.run_until_disconnected()
        except Exception as e:
            logger.error(f"❌ Failed to run bot for {c_id}: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [4] بوت الماستر الرئيسي (The Controller)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

master_bot = TelegramClient("TitanMaster", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@master_bot.on(events.NewMessage(pattern='/start'))
async def master_ui(event):
    if event.sender_id != MASTER_ID: return
    db = TitanDB.load()
    text = (f"👑 **لوحة تحكم إمبراطورية المصنع**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📱 حساباتك: `{len(db['master_accs'])}` | 💎 الزبائن: `{len(db['clients'])}` \n"
            f"🎯 الهدف: `{db['settings']['target']}` | ⏳ التأخير: `{db['settings']['delay']}`")
    btns = [
        [Button.inline("➕ ربط سيشن للماستر", "m_add_s"), Button.inline("🗑️ مسح حساب ماستر", "m_del_s")],
        [Button.inline("📊 عرض حساباتي", "m_list_s"), Button.inline("🔍 فحص الصلاحية", "m_check")],
        [Button.inline("🚀 بدء تجميع الماستر", "m_farm_menu"), Button.inline("⚙️ الإعدادات العامة", "m_set")],
        [Button.inline("💎 تنصيب لزبون جديد", "m_deploy"), Button.inline("🗑️ طرد زبون", "m_kick")],
        [Button.inline("📝 سجل العمليات", "m_logs"), Button.inline("🔄 ريستارت", "m_reboot")]
    ]
    await event.reply(text, buttons=btns)

@master_bot.on(events.CallbackQuery)
async def master_logic(event):
    if event.sender_id != MASTER_ID: return
    db = TitanDB.load(); cmd = event.data.decode()

    # --- [ نظام التنصيب المحدث والفحص العميق ] ---
    if cmd == "m_deploy":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("👤 **أرسل ID الزبون:**"); cid = (await conv.get_response()).text.strip()
            if not cid.isdigit(): return await conv.send_message("❌ الآيدي يجب أن يكون أرقاماً.")

            await conv.send_message("🔑 **أرسل توكن بوت الزبون:**"); ctok = (await conv.get_response()).text.strip()
            
            await conv.send_message("🔍 **جاري التحقق من التوكن وتشغيل النسخة...**")
            
            try:
                # محاولة تشغيل فعلية قبل الحفظ
                test_cl = TelegramClient(f"temp/test_{cid}", API_ID, API_HASH)
                await test_cl.start(bot_token=ctok)
                me = await test_cl.get_me()
                await test_cl.disconnect()
                
                await conv.send_message(f"⏳ **عدد أيام الترخيص:**"); cdays = (await conv.get_response()).text.strip()
                await conv.send_message(f"🔢 **حد الأرقام:**"); clim = (await conv.get_response()).text.strip()

                exp = (datetime.datetime.now() + datetime.timedelta(days=int(cdays))).strftime('%Y-%m-%d')
                db['clients'][cid] = {"token": ctok, "expiry": exp, "limit": int(clim), "accs": {}}
                TitanDB.save(db); TitanDB.add_log(f"تم تفعيل زبون: {cid}")
                
                # إطلاق المحرك فوراً
                asyncio.create_task(ClientBotRunner.start_instance(cid, ctok))
                
                await conv.send_message(f"✅ **تمت العملية بنجاح!**\n🤖 البوت: @{me.username}\n📅 الانتهاء: `{exp}`")
            except Exception as e:
                await conv.send_message(f"❌ **فشل التفعيل!**\nالسبب: التوكن غير شغال أو محظور.\n`{e}`")

    # --- [ بقية الأزرار المبرمجة بالكامل ] ---
    elif cmd == "m_add_s":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🔑 ارسل السيشن:"); ss = (await conv.get_response()).text.strip()
            await conv.send_message("📱 ارسل الرقم:"); ph = (await conv.get_response()).text.strip()
            db['master_accs'][ph] = ss; TitanDB.save(db); await conv.send_message("✅ تم الحفظ.")

    elif cmd == "m_del_s":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🗑️ ارسل الرقم لحذفه:"); ph = (await conv.get_response()).text.strip()
            if ph in db['master_accs']: 
                del db['master_accs'][ph]; TitanDB.save(db); await conv.send_message("✅ تم.")

    elif cmd == "m_list_s":
        m = "📊 **حسابات الماستر:**\n" + "\n".join([f"📱 `{p}`" for p in db['master_accs']]) if db['master_accs'] else "فارغة"
        await event.respond(m)

    elif cmd == "m_check":
        await event.answer("🔍 فحص الصلاحية...", alert=False)
        live, dead = 0, 0
        for ph, ss in db['master_accs'].copy().items():
            try:
                c = TelegramClient(StringSession(ss), API_ID, API_HASH)
                await c.connect()
                if await c.is_user_authorized(): live += 1
                else: (dead += 1, db['master_accs'].pop(ph))
                await c.disconnect()
            except: (dead += 1, db['master_accs'].pop(ph))
        TitanDB.save(db); await event.respond(f"✅ فحص: {live} شغال | {dead} طار")

    elif cmd == "m_farm_menu":
        btns = [[Button.inline("🔗 إحالة", "f_ref"), Button.inline("🎁 هدية", "f_gift")], [Button.inline("🔄 الكل", "f_all")]]
        await event.edit("🎯 اختر نوع التجميع لحسابات الماستر:", buttons=btns)

    elif cmd.startswith("f_"):
        mode = cmd.split("_")[-1]
        await event.answer("🚀 انطلق التجميع...", alert=True)
        for ph, ss in db['master_accs'].items():
            try:
                cl = TelegramClient(StringSession(ss), API_ID, API_HASH)
                await cl.connect()
                if mode in ["ref", "all"]:
                    u = db['settings']['ref'].split("/")[-1].split("?")[0]
                    p = db['settings']['ref'].split("start=")[-1]
                    await cl(functions.messages.StartBotRequest(bot=u, peer=u, start_param=p))
                if mode in ["gift", "all"]:
                    await cl.send_message(db['settings']['target'], "/start")
                await cl.disconnect(); await asyncio.sleep(db['settings']['delay'])
            except: pass
        await event.respond("🏁 انتهى تجميع الماستر.")

    elif cmd == "m_set":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🎯 يوزر الهدف:"); db['settings']['target'] = (await conv.get_response()).text.strip()
            await conv.send_message("🔗 رابط الإحالة:"); db['settings']['ref'] = (await conv.get_response()).text.strip()
            await conv.send_message("⏳ وقت التأخير:"); db['settings']['delay'] = int((await conv.get_response()).text.strip())
            TitanDB.save(db); await conv.send_message("✅ تم التحديث.")

    elif cmd == "m_logs":
        await event.respond("📝 **سجل العمليات:**\n\n" + "\n".join(db['logs']))

    elif cmd == "m_reboot":
        await event.answer("🔄 إعادة تشغيل...", alert=True)
        os.execl(sys.executable, sys.executable, *sys.argv)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [5] الإقلاع الذاتي عند بدء السيرفر
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main_boot():
    data = TitanDB.load()
    logger.info(f"System Boot: Re-launching {len(data['clients'])} instances...")
    for cid, info in data['clients'].items():
        # فحص الصلاحية قبل الإقلاع
        exp = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
        if datetime.datetime.now() < exp:
            asyncio.create_task(ClientBotRunner.start_instance(cid, info['token']))
    logger.info("👑 All systems are GO!")

if __name__ == "__main__":
    master_bot.loop.run_until_complete(main_boot())
    master_bot.run_until_disconnected()
