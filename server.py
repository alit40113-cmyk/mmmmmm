# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE IMPERIAL TITAN FACTORY - SUPREME EDITION 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- المطور الرئيسي: 8504553407
- الإصدار: 10.0 (Ultra Stable)
- الوظيفة: إدارة حسابات الماستر + مصنع بوتات الزبائن المقيد
- المميزات: فحص توكنات، فحص آيدي، محرك Bypass، سجلات حية
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
from telethon.errors import (
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    AccessTokenInvalidError,
    BotMethodInvalidError,
    SessionPasswordNeededError
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [1] إعدادات الهوية والبيئة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
BOT_TOKEN = "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY" 
MASTER_ID = 8504553407
DATABASE_NAME = "imperial_titan_db.json"

# إعداد السجلات الاحترافية (Logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.FileHandler('imperial_core.log'), logging.StreamHandler()]
)
logger = logging.getLogger("ImperialTitan")

# إنشاء المجلدات الضرورية
for folder in ["sessions", "instances", "backups"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [2] كلاس إدارة قاعدة البيانات (JSON DB Manager)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ImperialDatabase:
    """كلاس لإدارة عمليات الحفظ والقراءة وضمان سلامة البيانات"""
    
    def __init__(self, filename):
        self.filename = filename
        self._initialize_db()

    def _initialize_db(self):
        if not os.path.exists(self.filename):
            structure = {
                "config": {
                    "master_id": MASTER_ID,
                    "target_bot": "@t06bot",
                    "referral_link": "",
                    "delay": 45,
                    "system_status": "online"
                },
                "master_sessions": {}, # {phone: session_string}
                "clients": {}, # {id: {token, expiry, limit, accounts: {}}}
                "logs": [f"System initialized at {datetime.datetime.now()}"]
            }
            self.save(structure)

    def load(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Database Load Error: {e}")
            return {}

    def save(self, data):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Database Save Error: {e}")

    def add_event_log(self, text):
        data = self.load()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data['logs'].append(f"[{now}] {text}")
        if len(data['logs']) > 40:
            data['logs'].pop(0)
        self.save(data)

db_manager = ImperialDatabase(DATABASE_NAME)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [3] محرك التجميع والعمليات (The Core Engine)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class FarmingEngine:
    """محرك تنفيذ عمليات التجميع وتخطي الاشتراكات"""

    @staticmethod
    async def run_referral(client, ref_link):
        """تنفيذ عملية الإحالة"""
        try:
            if "start=" not in ref_link:
                return False, "رابط غير صالح"
            bot_u = ref_link.split("/")[-1].split("?")[0]
            param = ref_link.split("start=")[-1]
            await client(functions.messages.StartBotRequest(
                bot=bot_u, peer=bot_u, start_param=param
            ))
            return True, "نجاح"
        except Exception as e:
            return False, str(e)

    @staticmethod
    async def run_gift(client, target):
        """تنفيذ عملية الهدية اليومية مع تخطي القنوات"""
        try:
            await client.send_message(target, "/start")
            await asyncio.sleep(5)
            # محاولات التخطي (حلقة تكرارية لضمان الضغط)
            for _ in range(8):
                msgs = await client.get_messages(target, limit=1)
                if not msgs or not msgs[0].reply_markup:
                    break
                
                found_action = False
                for row in msgs[0].reply_markup.rows:
                    for btn in row.buttons:
                        if isinstance(btn, types.KeyboardButtonUrl):
                            try:
                                ch_name = btn.url.split('/')[-1]
                                await client(functions.channels.JoinChannelRequest(channel=ch_name))
                                found_action = True
                            except: pass
                        elif any(x in btn.text for x in ["تحقق", "تم", "تأكيد", "Verify"]):
                            await msgs[0].click(text=btn.text)
                            await asyncio.sleep(3)
                            found_action = True
                        elif any(x in btn.text for x in ["هدية", "يومية", "Gift", "Claim"]):
                            await msgs[0].click(text=btn.text)
                            return True, "تم الاستلام"
                if not found_action: break
            return False, "فشل التخطي"
        except Exception as e:
            return False, str(e)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [4] نظام إدارة بوتات الزبائن المستقلة (Bot Factory)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

active_instances = {}

async def launch_client_bot(c_id, c_token):
    """دالة تشغيل وإدارة دورة حياة بوت الزبون"""
    try:
        logger.info(f"--- [ Launching Bot for ID: {c_id} ] ---")
        client = TelegramClient(f"instances/bot_{c_id}", API_ID, API_HASH)
        await client.start(bot_token=c_token)
        active_instances[c_id] = client

        @client.on(events.NewMessage(pattern='/start'))
        async def sub_bot_start(event):
            if event.sender_id != int(c_id): return
            data = db_manager.load()
            info = data['clients'].get(str(c_id))
            if not info: return
            
            # فحص انتهاء الترخيص
            expiry = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
            if datetime.datetime.now() > expiry:
                return await event.reply("❌ **انتهى اشتراكك!**\nيرجى مراسلة المطور للتجديد.")

            panel_text = (
                f"🛡️ **لوحة التحكم الخاصة بك**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 معرفك: `{c_id}`\n"
                f"📅 انتهاء الاشتراك: `{info['expiry']}`\n"
                f"🔢 الحسابات المربوطة: `{len(info['accounts'])} / {info['limit']}`\n"
                f"🎯 الهدف العالمي: `{data['config']['target_bot']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            btns = [
                [Button.inline("➕ إضافة حساب جديد", "sub_add"), Button.inline("🗑️ مسح حساب", "sub_del")],
                [Button.inline("🚀 بدء تجميع الإحالة", "sub_ref"), Button.inline("🎁 بدء تجميع الهدية", "sub_gift")],
                [Button.inline("🔄 تجميع شامل", "sub_all")],
                [Button.inline("📊 عرض أرقامي المربوطة", "sub_list")]
            ]
            await event.reply(panel_text, buttons=btns)

        @client.on(events.CallbackQuery)
        async def sub_bot_callback(event):
            cid_str = str(event.sender_id)
            db_data = db_manager.load()
            query = event.data.decode()

            if query == "sub_add":
                if len(db_data['clients'][cid_str]['accounts']) >= db_data['clients'][cid_str]['limit']:
                    return await event.answer("❌ وصلت للحد الأقصى المسموح به!", alert=True)
                
                async with client.conversation(event.sender_id) as conv:
                    await conv.send_message("🔑 **يرجى إرسال الـ String Session:**")
                    ss = (await conv.get_response()).text.strip()
                    await conv.send_message("📱 **يرجى إرسال رقم الهاتف:**")
                    ph = (await conv.get_response()).text.strip()
                    db_data['clients'][cid_str]['accounts'][ph] = ss
                    db_manager.save(db_data)
                    await conv.send_message(f"✅ تم ربط الحساب `{ph}` بنجاح.")

            elif query == "sub_del":
                async with client.conversation(event.sender_id) as conv:
                    await conv.send_message("🗑️ **أرسل الرقم المراد حذفه:**")
                    target = (await conv.get_response()).text.strip()
                    if target in db_data['clients'][cid_str]['accounts']:
                        del db_data['clients'][cid_str]['accounts'][target]
                        db_manager.save(db_data)
                        await conv.send_message(f"✅ تم حذف الرقم `{target}`.")
                    else:
                        await conv.send_message("❌ هذا الرقم غير موجود في قائمتك.")

            elif query == "sub_list":
                my_accs = db_data['clients'][cid_str]['accounts']
                if not my_accs: return await event.respond("📊 ليس لديك أي حسابات.")
                msg = "📊 **قائمة حساباتك:**\n\n" + "\n".join([f"📱 `{p}`" for p in my_accs])
                await event.respond(msg)

            elif query.startswith("sub_"):
                mode = query.split("_")[-1]
                await event.answer("🚀 بدأ محرك التجميع...", alert=False)
                for ph, ss in db_data['clients'][cid_str]['accounts'].items():
                    try:
                        cl_temp = TelegramClient(StringSession(ss), API_ID, API_HASH)
                        await cl_temp.connect()
                        if mode in ["ref", "all"]:
                            await FarmingEngine.run_referral(cl_temp, db_data['config']['referral_link'])
                        if mode in ["gift", "all"]:
                            await FarmingEngine.run_gift(cl_temp, db_data['config']['target_bot'])
                        await cl_temp.disconnect()
                        await asyncio.sleep(db_data['config']['delay'])
                    except: continue
                await event.respond("🏁 **انتهت المهمة لجميع حساباتك.**")

        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Instance Error for {c_id}: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [5] بوت الماستر الرئيسي (The Imperial Master)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

master_bot = TelegramClient("Imperial_Master_Core", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@master_bot.on(events.NewMessage(pattern='/start'))
async def master_start(event):
    if event.sender_id != MASTER_ID: return
    data = db_manager.load()
    dashboard = (
        f"👑 **مرحباً بك في مصنع الإمبراطورية**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 حساباتك الخاصة: `{len(data['master_sessions'])}` \n"
        f"💎 الزبائن المفعّلين: `{len(data['clients'])}` \n"
        f"⚙️ الهدف: `{data['config']['target_bot']}`\n"
        f"⏳ التأخير: `{data['config']['delay']} ثانية` \n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    btns = [
        [Button.inline("➕ ربط سيشن للماستر", "m_add_ss"), Button.inline("🗑️ مسح حساب ماستر", "m_del_ss")],
        [Button.inline("📊 عرض حساباتي", "m_view_accs"), Button.inline("🔍 فحص الصلاحية", "m_audit")],
        [Button.inline("🚀 بدء تجميع الماستر", "m_farm_menu"), Button.inline("⚙️ الإعدادات العامة", "m_settings")],
        [Button.inline("💎 تنصيب لزبون جديد", "m_deploy"), Button.inline("🗑️ طرد زبون", "m_kick")],
        [Button.inline("📝 سجل العمليات", "m_logs"), Button.inline("📩 أداة الاستخراج", "m_tool")],
        [Button.inline("🔄 إعادة تشغيل النظام", "m_reboot")]
    ]
    await event.reply(dashboard, buttons=btns)

@master_bot.on(events.CallbackQuery)
async def master_callback(event):
    if event.sender_id != MASTER_ID: return
    data = db_manager.load()
    query = event.data.decode()

    # --- [ 1. نظام التنصيب والفحص الدقيق ] ---
    if query == "m_deploy":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("👤 **أرسل ID الزبون (يجب أن يكون رقماً):**")
            cid = (await conv.get_response()).text.strip()
            if not cid.isdigit(): return await conv.send_message("❌ خطأ: الآيدي غير صالح.")

            await conv.send_message("🔑 **أرسل توكن البوت الخاص بالزبون:**")
            ctok = (await conv.get_response()).text.strip()
            
            await conv.send_message("🔍 **جاري فحص التوكن وتشغيل النسخة...**")
            try:
                # محاولة فحص التوكن عبر GetMe
                checker = TelegramClient(f"temp/test_{cid}", API_ID, API_HASH)
                await checker.start(bot_token=ctok)
                me = await checker.get_me()
                await checker.disconnect()
                
                await conv.send_message(f"✅ تم التحقق: @{me.username}\n⏳ **أرسل عدد أيام الاشتراك:**")
                days = (await conv.get_response()).text.strip()
                await conv.send_message("🔢 **أرسل حد الأرقام المسموح له:**")
                lim = (await conv.get_response()).text.strip()

                expiry = (datetime.datetime.now() + datetime.timedelta(days=int(days))).strftime('%Y-%m-%d')
                data['clients'][cid] = {"token": ctok, "expiry": expiry, "limit": int(lim), "accounts": {}}
                db_manager.save(data)
                db_manager.add_event_log(f"تم تنصيب زبون جديد: {cid}")
                
                # إطلاق المحرك فوراً
                asyncio.create_task(launch_client_bot(cid, ctok))
                await conv.send_message("🎉 **تم تفعيل البوت وتشغيله بنجاح!**")
            except Exception as e:
                await conv.send_message(f"❌ فشل: التوكن غير صالح أو محظور.\n`{e}`")

    # --- [ 2. إدارة حسابات الماستر ] ---
    elif query == "m_add_ss":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🔑 **أرسل السيشن سترينج:**")
            ss = (await conv.get_response()).text.strip()
            await conv.send_message("📱 **أرسل الرقم:**")
            ph = (await conv.get_response()).text.strip()
            data['master_sessions'][ph] = ss
            db_manager.save(data); await conv.send_message("✅ تم الإضافة للماستر.")

    elif query == "m_del_ss":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🗑️ **أرسل الرقم لحذفه:**")
            ph = (await conv.get_response()).text.strip()
            if ph in data['master_sessions']:
                del data['master_sessions'][ph]; db_manager.save(data); await conv.send_message("✅ تم الحذف.")

    elif query == "m_view_accs":
        m = "📊 **حساباتك:**\n" + "\n".join([f"📱 `{p}`" for p in data['master_sessions']]) if data['master_sessions'] else "لا يوجد"
        await event.respond(m)

    elif query == "m_audit":
        await event.answer("🔍 جاري فحص الحسابات...", alert=False)
        live, dead = 0, 0
        for ph, ss in data['master_sessions'].copy().items():
            try:
                c = TelegramClient(StringSession(ss), API_ID, API_HASH)
                await c.connect()
                if await c.is_user_authorized(): live += 1
                else: (dead += 1, data['master_sessions'].pop(ph))
                await c.disconnect()
            except: (dead += 1, data['master_sessions'].pop(ph))
        db_manager.save(data); await event.respond(f"✅ فحص الماستر:\n🟢 شغال: {live}\n🔴 طار: {dead}")

    # --- [ 3. التجميع والإعدادات ] ---
    elif query == "m_farm_menu":
        btns = [[Button.inline("🔗 إحالة", "mf_ref"), Button.inline("🎁 هدية", "mf_gift")], [Button.inline("🔄 الكل", "mf_all")]]
        await event.edit("🎯 اختر نوع التجميع لحساباتك:", buttons=btns)

    elif query.startswith("mf_"):
        mode = query.split("_")[-1]
        await event.answer("🚀 انطلق التجميع...", alert=True)
        for ph, ss in data['master_sessions'].items():
            try:
                cl = TelegramClient(StringSession(ss), API_ID, API_HASH)
                await cl.connect()
                if mode in ["ref", "all"]: await FarmingEngine.run_referral(cl, data['config']['referral_link'])
                if mode in ["gift", "all"]: await FarmingEngine.run_gift(cl, data['config']['target_bot'])
                await cl.disconnect(); await asyncio.sleep(data['config']['delay'])
            except: continue
        await event.respond("🏁 اكتمل تجميع الماستر.")

    elif query == "m_settings":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🎯 يوزر الهدف:"); data['config']['target_bot'] = (await conv.get_response()).text.strip()
            await conv.send_message("🔗 رابط الإحالة:"); data['config']['referral_link'] = (await conv.get_response()).text.strip()
            await conv.send_message("⏳ التأخير:"); data['config']['delay'] = int((await conv.get_response()).text.strip())
            db_manager.save(data); await conv.send_message("✅ تم التحديث.")

    elif query == "m_logs":
        await event.respond("📝 **سجل العمليات الأخير:**\n\n" + "\n".join(data['logs']))

    elif query == "m_tool":
        code = f"from telethon import TelegramClient\nimport asyncio\nasync def x():\n async with TelegramClient(None, {API_ID}, '{API_HASH}') as c: print(c.session.save())\nasyncio.run(x())"
        with open("GetSession.py", "w") as f: f.write(code)
        await event.respond("🛠 أداة استخراج السيشن:", file="GetSession.py")

    elif query == "m_reboot":
        await event.answer("🔄 جاري إعادة التشغيل...", alert=True)
        os.execl(sys.executable, sys.executable, *sys.argv)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [6] نظام الإقلاع الآلي (Boot Loader)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def system_startup():
    """تشغيل كافة البوتات الفرعية عند بدء السيرفر"""
    logger.info("--- [ SYSTEM STARTUP INITIATED ] ---")
    data = db_manager.load()
    for cid, info in data['clients'].items():
        # التأكد من عدم انتهاء الصلاحية قبل التشغيل
        exp_dt = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
        if datetime.datetime.now() < exp_dt:
            asyncio.create_task(launch_client_bot(cid, info['token']))
    logger.info("--- [ ALL INSTANCES ARE ONLINE ] ---")

if __name__ == "__main__":
    master_bot.loop.run_until_complete(system_startup())
    master_bot.run_until_disconnected()
