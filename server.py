# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE SUPREME IMPERIAL FACTORY - ULTIMATE EDITION 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- المطور الرئيسي: 8504553407
- النسخة: V12.0.5 (Enterprise)
- الوظيفة: مصنع بوتات تجميع متكامل مع نظام تراخيص مشدد.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os, sys, json, asyncio, datetime, random, logging, re, time
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import *
from telethon.utils import get_display_name

# --- [ إعدادات الاتصال الأساسية ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
BOT_TOKEN = "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY" 
MASTER_ID = 8504553407
DB_FILE = "imperial_master_core.json"

# --- [ تهيئة نظام السجلات الاحترافي ] ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("ImperialFactory")

# --- [ محرك إدارة البيانات العملاق ] ---
class DatabaseManager:
    def __init__(self, path):
        self.path = path
        self.initialize()

    def initialize(self):
        if not os.path.exists(self.path):
            structure = {
                "config": {"target": "@t06bot", "ref": "", "delay": 45},
                "clients": {}, # { "id": { "token": "", "expiry": "", "limit": 0, "accounts": {} } }
                "stats": {"total_users": 0, "total_accs": 0, "ops": 0},
                "logs": [f"System Boot: {datetime.datetime.now()}"]
            }
            self.save(structure)

    def get_data(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}

    def save(self, data):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

db_manager = DatabaseManager(DB_FILE)

# --- [ محاكي بصمة الأجهزة - لمنع الحظر ] ---
def get_device_meta():
    brands = [
        {"dm": "iPhone 15 Pro Max", "sv": "17.4", "av": "10.1.1"},
        {"dm": "Samsung S24 Ultra", "sv": "14.0", "av": "10.0.5"},
        {"dm": "Pixel 8 Pro", "sv": "14.1", "av": "9.8.2"},
        {"dm": "iPad Pro M2", "sv": "17.1", "av": "10.2.0"}
    ]
    return random.choice(brands)

# --- [ محرك التجميع الذكي ] ---
async def perform_collect(client, mode, target, ref, log_list):
    try:
        # الطريقة الأولى: الإحالة
        if mode in ["ref", "both"] and ref:
            try:
                bot_user = ref.split("/")[-1].split("?")[0]
                start_param = ref.split("start=")[-1]
                await client(functions.messages.StartBotRequest(bot=bot_user, peer=bot_user, start_param=start_param))
                log_list.append(f"🔗 Success Referral: {bot_user}")
            except: pass

        # الطريقة الثانية: الهدية اليومية (Bypass)
        if mode in ["gift", "both"]:
            await client.send_message(target, "/start")
            await asyncio.sleep(5)
            for _ in range(10): # محاولات تخطي الاشتراك
                history = await client.get_messages(target, limit=1)
                if not history or not history[0].reply_markup: break
                
                clicked = False
                for row in history[0].reply_markup.rows:
                    for btn in row.buttons:
                        if isinstance(btn, types.KeyboardButtonUrl):
                            try: await client(functions.channels.JoinChannelRequest(btn.url.split('/')[-1]))
                            except: pass
                            clicked = True
                        elif any(x in btn.text for x in ["تحقق", "تم", "تأكيد"]):
                            await history[0].click(text=btn.text)
                            await asyncio.sleep(3)
                            clicked = True
                        elif any(x in btn.text for x in ["هدية", "Daily", "يومية"]):
                            await history[0].click(text=btn.text)
                            log_list.append("🎁 Daily Gift Collected.")
                            return True
                if not clicked: break
        return True
    except Exception as e:
        log_list.append(f"❌ Operation Error: {str(e)[:50]}")
        return False

# --- [ محرك تشغيل بوتات الزبائن (Sub-Bot Engine) ] ---
async def start_client_instance(client_id, token):
    try:
        cbot = TelegramClient(f"instance_{client_id}", API_ID, API_HASH)
        await cbot.start(bot_token=token)
        
        @cbot.on(events.NewMessage(pattern='/start'))
        async def client_start_ui(event):
            if event.sender_id != int(client_id): return
            data = db_manager.get_data()
            info = data['clients'].get(str(client_id))
            if not info: return
            
            # فحص الترخيص
            exp_dt = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
            if datetime.datetime.now() > exp_dt:
                return await event.reply("⚠️ انتهى اشتراكك! يرجى التواصل مع المالك للتجديد.")

            status_text = (
                f"💎 **مرحباً بك في لوحة تحكم الزبون**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏳ اشتراكك ينتهي في: `{info['expiry']}`\n"
                f"🔢 حد الأرقام: `{len(info['accounts'])} / {info['limit']}`\n"
                f"🎯 هدف التجميع: `{data['config']['target']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            btns = [
                [Button.inline("➕ إضافة رقم جديد", "c_add"), Button.inline("🗑️ مسح رقم", "c_del")],
                [Button.inline("🚀 بدء تجميع (إحالة)", "c_farm_ref"), Button.inline("🎁 بدء تجميع (هدية)", "c_farm_gift")],
                [Button.inline("🔄 تجميع شامل", "c_farm_all")],
                [Button.inline("📊 عرض حساباتي", "c_list")]
            ]
            await event.reply(status_text, buttons=btns)

        @cbot.on(events.CallbackQuery)
        async def client_actions(event):
            cid = str(event.sender_id)
            data = db_manager.get_data()
            if cid not in data['clients']: return
            cmd = event.data.decode()

            if cmd == "c_add":
                if len(data['clients'][cid]['accounts']) >= data['clients'][cid]['limit']:
                    return await event.answer("❌ عذراً، وصلت للحد الأقصى المسموح لك!", alert=True)
                async with cbot.conversation(event.sender_id) as conv:
                    await conv.send_message("🔑 أرسل الـ String Session الآن:"); ss = (await conv.get_response()).text.strip()
                    await conv.send_message("📱 أرسل رقم الهاتف:"); ph = (await conv.get_response()).text.strip()
                    data['clients'][cid]['accounts'][ph] = ss
                    db_manager.save(data); await conv.send_message("✅ تم إضافة الحساب لنسختك.")

            elif cmd == "c_del":
                async with cbot.conversation(event.sender_id) as conv:
                    await conv.send_message("🗑️ أرسل الرقم لمسحه:"); ph = (await conv.get_response()).text.strip()
                    if ph in data['clients'][cid]['accounts']:
                        del data['clients'][cid]['accounts'][ph]
                        db_manager.save(data); await conv.send_message("✅ تم الحذف.")
                    else: await conv.send_message("❌ الرقم غير موجود.")

            elif cmd.startswith("c_farm_"):
                mode = cmd.split("_")[-1]
                await event.answer("🚀 بدأت العملية بحساباتك...", alert=False)
                for ph, ss in data['clients'][cid]['accounts'].items():
                    cl = TelegramClient(StringSession(ss), API_ID, API_HASH)
                    await cl.connect()
                    await perform_collect(cl, mode, data['config']['target'], data['config']['ref'], data['logs'])
                    await cl.disconnect(); await asyncio.sleep(2)
                await event.respond("🏁 انتهى التجميع لجميع حساباتك.")

            elif cmd == "c_list":
                msg = "📊 **أرقامك المربوطة:**\n\n" + "\n".join([f"📱 `{p}`" for p in data['clients'][cid]['accounts']])
                await event.respond(msg if data['clients'][cid]['accounts'] else "لا يوجد أرقام.")

        await cbot.run_until_disconnected()
    except: pass

# --- [ بوت الماستر (المصنع الرئيسي) ] ---
master_bot = TelegramClient("MasterCore", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@master_bot.on(events.NewMessage(pattern='/start'))
async def master_main(event):
    if event.sender_id != MASTER_ID: return
    data = db_manager.get_data()
    text = (
        f"👑 **لوحة تحكم المصنع الإمبراطوري** 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 الزبائن النشطين: `{len(data['clients'])}` \n"
        f"⚙️ الهدف الحالي: `{data['config']['target']}`\n"
        f"🔗 الإحالة: `{data['config']['ref'][:20]}...`"
    )
    btns = [
        [Button.inline("💎 تنصيب نسخة زبون", "m_deploy")],
        [Button.inline("📊 إدارة الزبائن", "m_clients"), Button.inline("🗑️ حذف زبون", "m_kick")],
        [Button.inline("⚙️ إعدادات التجميع", "m_conf"), Button.inline("📝 السجلات", "m_logs")],
        [Button.inline("🔍 أداة الاستخراج", "m_tool")]
    ]
    await event.reply(text, buttons=btns)

@master_bot.on(events.CallbackQuery)
async def master_handler(event):
    if event.sender_id != MASTER_ID: return
    data = db_manager.get_data()
    cmd = event.data.decode()

    if cmd == "m_deploy":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("👤 أرسل ID الزبون:"); cid = (await conv.get_response()).text.strip()
            await conv.send_message("🔑 أرسل توكن بوت الزبون:"); ctok = (await conv.get_response()).text.strip()
            await conv.send_message("⏳ مدة الترخيص (أيام):"); cday = (await conv.get_response()).text.strip()
            await conv.send_message("🔢 حد الأرقام المسموح له:"); clim = (await conv.get_response()).text.strip()
            
            exp = (datetime.datetime.now() + datetime.timedelta(days=int(cday))).strftime('%Y-%m-%d')
            data['clients'][cid] = {"token": ctok, "expiry": exp, "limit": int(clim), "accounts": {}}
            db_manager.save(data)
            
            asyncio.create_task(start_client_instance(cid, ctok))
            await conv.send_message(f"✅ تم تنصيب بوت الزبون {cid} بنجاح!\n📅 ينتهي: {exp}\n🔢 الحد: {clim}")

    elif cmd == "m_conf":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🎯 أرسل يوزر الهدف الجديد:"); data['config']['target'] = (await conv.get_response()).text.strip()
            await conv.send_message("🔗 أرسل رابط الإحالة الجديد:"); data['config']['ref'] = (await conv.get_response()).text.strip()
            db_manager.save(data); await conv.send_message("✅ تم التحديث.")

    elif cmd == "m_clients":
        msg = "📊 **قائمة الزبائن:**\n\n"
        for k, v in data['clients'].items():
            msg += f"👤 ID: `{k}`\n📅 Exp: `{v['expiry']}`\n🔢 Limit: `{v['limit']}`\n\n"
        await event.respond(msg if data['clients'] else "لا يوجد زبائن.")

    elif cmd == "m_tool":
        code = f"import asyncio\nfrom telethon import TelegramClient\nasync def x():\n async with TelegramClient(None, {API_ID}, '{API_HASH}') as c: print(c.session.save())\nasyncio.run(x())"
        with open("GetSession.py", "w") as f: f.write(code)
        await event.respond("🛠 ملف استخراج السيشن للزبائن:", file="GetSession.py")

async def boot_all():
    data = db_manager.get_data()
    for cid, info in data['clients'].items():
        asyncio.create_task(start_client_instance(cid, info['token']))

print("👑 Factory Server is Running...")
master_bot.loop.run_until_complete(boot_all())
master_bot.run_until_disconnected()
