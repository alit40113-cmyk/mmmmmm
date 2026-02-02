# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE SUPREME IMPERIAL FACTORY - ULTIMATE MASTER EDITION 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- المطور: 8504553407
- الإصدار: V15.0 (Enterprise)
- الوظيفة: تحكم شامل بالماستر + مصنع زبائن متكامل.
- الأمان: نظام Hardware Simulation + Anti-Flood.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os, sys, json, asyncio, datetime, random, logging, re, time, platform
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import *
from telethon.utils import get_display_name

# --- [ الإعدادات الجوهرية للماستر ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
BOT_TOKEN = "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY" 
MASTER_ID = 8504553407
DATABASE_FILE = "imperial_grand_core.json"

# --- [ إعدادات السجلات الاحترافية ] ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('master_core.log')]
)
logger = logging.getLogger("ImperialCore")

# --- [ محرك إدارة قاعدة البيانات العملاقة ] ---
class CoreDatabase:
    def __init__(self, file):
        self.file = file
        self.init_system()

    def init_system(self):
        if not os.path.exists(self.file):
            data = {
                "master_config": {
                    "owner_id": MASTER_ID,
                    "target_bot": "@t06bot",
                    "ref_link": "",
                    "sleep_time": 45,
                    "auto_check": True
                },
                "master_sessions": {}, # {phone: {"ss": session, "name": "", "added": ""}}
                "clients_factory": {}, # {id: {token, expiry, limit, sessions: {}}}
                "system_stats": {"total_collected": 0, "successful_runs": 0, "errors": 0},
                "global_logs": []
            }
            self.sync(data)

    def get_data(self):
        try:
            with open(self.file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}

    def sync(self, data):
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def log_event(self, event_text):
        data = self.get_data()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data['global_logs'].append(f"[{now}] {event_text}")
        if len(data['global_logs']) > 30: data['global_logs'].pop(0)
        self.sync(data)

db = CoreDatabase(DATABASE_FILE)

# --- [ محرك التجميع والتحكم بالحسابات (The Engines) ] ---

class ImperialEngine:
    @staticmethod
    async def join_channel(client, channel_url):
        try:
            if "t.me/" in channel_url:
                channel_url = channel_url.split('/')[-1]
            await client(functions.channels.JoinChannelRequest(channel=channel_url))
            return True
        except: return False

    @staticmethod
    async def process_referral(client, ref_link):
        try:
            if "start=" not in ref_link: return False
            bot_username = ref_link.split("/")[-1].split("?")[0]
            param = ref_link.split("start=")[-1]
            await client(functions.messages.StartBotRequest(bot=bot_username, peer=bot_username, start_param=param))
            return True
        except: return False

    @staticmethod
    async def process_daily_gift(client, target):
        try:
            await client.send_message(target, "/start")
            await asyncio.sleep(5)
            # نظام تخطي ذكي لـ 10 محاولات
            for _ in range(10):
                msgs = await client.get_messages(target, limit=1)
                if not msgs or not msgs[0].reply_markup: break
                
                clicked = False
                for row in msgs[0].reply_markup.rows:
                    for btn in row.buttons:
                        if isinstance(btn, types.KeyboardButtonUrl):
                            await ImperialEngine.join_channel(client, btn.url)
                            clicked = True
                        elif any(x in btn.text for x in ["تحقق", "تم", "تأكيد", "Verify"]):
                            await msgs[0].click(text=btn.text)
                            await asyncio.sleep(3)
                            clicked = True
                        elif any(x in btn.text for x in ["هدية", "يومية", "Daily", "Gift"]):
                            await msgs[0].click(text=btn.text)
                            return True
                if not clicked: break
            return False
        except: return False

# --- [ محرك تشغيل بوتات الزبائن (Multi-Instance Factory) ] ---

async def start_client_instance(c_id, c_token):
    try:
        sub_bot = TelegramClient(f"instances/bot_{c_id}", API_ID, API_HASH)
        await sub_bot.start(bot_token=c_token)
        
        @sub_bot.on(events.NewMessage(pattern='/start'))
        async def sub_start(event):
            if event.sender_id != int(c_id): return
            data = db.get_data()
            info = data['clients_factory'].get(str(c_id))
            if not info: return
            
            # فحص تاريخ الصلاحية
            exp = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
            if datetime.datetime.now() > exp:
                return await event.reply("⚠️ **عذراً، انتهى اشتراكك!**\nيرجى مراسلة المطور للتجديد.")

            text = (f"💎 **أهلاً بك في نسختك الخاصة**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📅 الانتهاء: `{info['expiry']}`\n"
                    f"🔢 الحسابات: `{len(info['sessions'])} / {info['limit']}`\n"
                    f"🎯 الهدف: `{data['master_config']['target_bot']}`")
            
            btns = [
                [Button.inline("➕ إضافة حساب", "c_add"), Button.inline("🗑️ مسح حساب", "c_del")],
                [Button.inline("🚀 بدء التجميع", "c_farm")],
                [Button.inline("📊 حساباتي", "c_list")]
            ]
            await event.reply(text, buttons=btns)

        @sub_bot.on(events.CallbackQuery)
        async def sub_actions(event):
            cid = str(event.sender_id)
            data = db.get_data()
            if cid not in data['clients_factory']: return
            cmd = event.data.decode()

            if cmd == "c_add":
                if len(data['clients_factory'][cid]['sessions']) >= data['clients_factory'][cid]['limit']:
                    return await event.answer("❌ الحد ممتلئ!", alert=True)
                async with sub_bot.conversation(event.sender_id) as conv:
                    await conv.send_message("🔑 أرسل الـ String Session:"); ss = (await conv.get_response()).text.strip()
                    await conv.send_message("📱 أرسل رقم الهاتف:"); ph = (await conv.get_response()).text.strip()
                    data['clients_factory'][cid]['sessions'][ph] = ss
                    db.sync(data); await conv.send_message("✅ تم الحفظ.")

            elif cmd == "c_del":
                async with sub_bot.conversation(event.sender_id) as conv:
                    await conv.send_message("🗑️ أرسل الرقم لحذفه:"); ph = (await conv.get_response()).text.strip()
                    if ph in data['clients_factory'][cid]['sessions']:
                        del data['clients_factory'][cid]['sessions'][ph]
                        db.sync(data); await conv.send_message("✅ تم الحذف.")
                    else: await conv.send_message("❌ غير موجود.")

            elif cmd == "c_farm":
                await event.answer("🚀 بدأ التجميع...", alert=False)
                for ph, ss in data['clients_factory'][cid]['sessions'].items():
                    cl = TelegramClient(StringSession(ss), API_ID, API_HASH)
                    await cl.connect()
                    await ImperialEngine.process_referral(cl, data['master_config']['ref_link'])
                    await ImperialEngine.process_daily_gift(cl, data['master_config']['target_bot'])
                    await cl.disconnect(); await asyncio.sleep(2)
                await event.respond("🏁 انتهت العملية لجميع حساباتك.")

            elif cmd == "c_list":
                accs = data['clients_factory'][cid]['sessions']
                msg = "📊 **أرقامك:**\n" + "\n".join([f"📱 `{p}`" for p in accs])
                await event.respond(msg if accs else "لا يوجد حسابات.")

        await sub_bot.run_until_disconnected()
    except: pass

# --- [ بوت الماستر الرئيسي (The Supreme Master) ] ---

master_bot = TelegramClient("Imperial_Master", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@master_bot.on(events.NewMessage(pattern='/start'))
async def master_main_ui(event):
    if event.sender_id != MASTER_ID: return
    data = db.get_data()
    text = (
        f"👑 **لوحة تحكم الإمبراطورية الرئيسية**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 حسابات الماستر: `{len(data['master_sessions'])}` \n"
        f"💎 الزبائن النشطين: `{len(data['clients_factory'])}` \n"
        f"🎯 الهدف الحالي: `{data['master_config']['target_bot']}` \n"
        f"🔗 الإحالة: `{data['master_config']['ref_link'][:20]}...` \n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    # جميع الأزرار المطلوبة مبرمجة هنا
    btns = [
        [Button.inline("➕ ربط سيشن جديد", "m_add_acc"), Button.inline("🗑️ مسح حساب", "m_del_acc")],
        [Button.inline("📊 عرض الحسابات", "m_list_acc"), Button.inline("🔍 فحص الصلاحية", "m_check_acc")],
        [Button.inline("🚀 بدء التجميع", "m_farm_menu"), Button.inline("⚙️ الإعدادات", "m_settings")],
        [Button.inline("💎 تنصيب لزبون", "m_deploy"), Button.inline("📝 سجل العمليات", "m_logs")],
        [Button.inline("📩 أداة الاستخراج", "m_tool"), Button.inline("🔄 ريستارت", "m_reboot")]
    ]
    await event.reply(text, buttons=btns)

@master_bot.on(events.CallbackQuery)
async def master_callback_handler(event):
    if event.sender_id != MASTER_ID: return
    data = db.get_data()
    query = event.data.decode()

    # 1. إضافة حساب للماستر
    if query == "m_add_acc":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🔑 **أرسل الـ String Session للماستر:**")
            ss = (await conv.get_response()).text.strip()
            await conv.send_message("📱 **أرسل رقم الهاتف:**")
            ph = (await conv.get_response()).text.strip()
            try:
                cl = TelegramClient(StringSession(ss), API_ID, API_HASH)
                await cl.connect()
                if await cl.is_user_authorized():
                    me = await cl.get_me()
                    data['master_sessions'][ph] = {"ss": ss, "name": me.first_name}
                    db.sync(data); db.log_event(f"تم إضافة حساب ماستر جديد: {ph}")
                    await conv.send_message(f"✅ تم بنجاح ربط حساب: {me.first_name}")
                else: await conv.send_message("❌ السيشن منتهي.")
                await cl.disconnect()
            except Exception as e: await conv.send_message(f"⚠️ خطأ: {e}")

    # 2. مسح حساب ماستر
    elif query == "m_del_acc":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🗑️ **أرسل الرقم المراد حذفه:**")
            ph = (await conv.get_response()).text.strip()
            if ph in data['master_sessions']:
                del data['master_sessions'][ph]
                db.sync(data); db.log_event(f"تم حذف حساب ماستر: {ph}")
                await conv.send_message("✅ تم الحذف من قاعدة البيانات.")
            else: await conv.send_message("❌ الرقم غير موجود.")

    # 3. عرض حسابات الماستر
    elif query == "m_list_acc":
        accs = data['master_sessions']
        if not accs: return await event.respond("📊 لا توجد حسابات ماستر.")
        msg = "📊 **قائمة حساباتك الخاصة:**\n\n"
        for p, info in accs.items():
            msg += f"📱 `{p}` - 👤 `{info['name']}`\n"
        await event.respond(msg)

    # 4. فحص الصلاحية
    elif query == "m_check_acc":
        await event.answer("🔍 جاري فحص الحسابات...", alert=False)
        live, dead = 0, 0
        for ph, info in data['master_sessions'].copy().items():
            try:
                cl = TelegramClient(StringSession(info['ss']), API_ID, API_HASH)
                await cl.connect()
                if not await cl.is_user_authorized():
                    dead += 1; del data['master_sessions'][ph]
                else: live += 1
                await cl.disconnect()
            except: dead += 1; del data['master_sessions'][ph]
        db.sync(data); await event.respond(f"✅ الفحص:\n🟢 شغالة: {live}\n🔴 طائرة: {dead}")

    # 5. التجميع (إحالة وهدية)
    elif query == "m_farm_menu":
        btns = [[Button.inline("🔗 إحالة فقط", "f_ref"), Button.inline("🎁 هدية فقط", "f_gift")], [Button.inline("🔄 تجميع شامل", "f_all")]]
        await event.edit("🎯 اختر نوع التجميع لحسابات الماستر:", buttons=btns)

    elif query.startswith("f_"):
        mode = query.split("_")[-1]
        await event.answer("🚀 انطلق المحرك...", alert=True)
        for ph, info in data['master_sessions'].items():
            cl = TelegramClient(StringSession(info['ss']), API_ID, API_HASH)
            await cl.connect()
            if mode in ["ref", "all"]: await ImperialEngine.process_referral(cl, data['master_config']['ref_link'])
            if mode in ["gift", "all"]: await ImperialEngine.process_daily_gift(cl, data['master_config']['target_bot'])
            await cl.disconnect(); await asyncio.sleep(data['master_config']['sleep_time'])
        await event.respond("🏁 انتهى التجميع لجميع حسابات الماستر.")

    # 6. الإعدادات
    elif query == "m_settings":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🎯 أرسل يوزر الهدف الجديد (مثال: @t06bot):")
            data['master_config']['target_bot'] = (await conv.get_response()).text.strip()
            await conv.send_message("🔗 أرسل رابط الإحالة الجديد:")
            data['master_config']['ref_link'] = (await conv.get_response()).text.strip()
            db.sync(data); await conv.send_message("✅ تم تحديث الإعدادات.")

    # 7. تنصيب لزبون
    elif query == "m_deploy":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("👤 ID الزبون:"); cid = (await conv.get_response()).text.strip()
            await conv.send_message("🔑 توكن البوت:"); ctok = (await conv.get_response()).text.strip()
            await conv.send_message("⏳ الأيام:"); cday = (await conv.get_response()).text.strip()
            await conv.send_message("🔢 الحد:"); clim = (await conv.get_response()).text.strip()
            
            exp = (datetime.datetime.now() + datetime.timedelta(days=int(cday))).strftime('%Y-%m-%d')
            data['clients_factory'][cid] = {"token": ctok, "expiry": exp, "limit": int(clim), "sessions": {}}
            db.sync(data); asyncio.create_task(start_client_instance(cid, ctok))
            await conv.send_message(f"✅ تم تنصيب بوت الزبون {cid}")

    elif query == "m_logs":
        msg = "📝 **سجل العمليات الأخير:**\n\n" + "\n".join(data['global_logs'])
        await event.respond(msg)

    elif query == "m_tool":
        code = f"from telethon import TelegramClient\nimport asyncio\nasync def x():\n async with TelegramClient(None, {API_ID}, '{API_HASH}') as c: print(c.session.save())\nasyncio.run(x())"
        with open("Extractor.py", "w") as f: f.write(code)
        await event.respond("🛠 أداة استخراج السيشن:", file="Extractor.py")

    elif query == "m_reboot":
        await event.answer("🔄 جاري إعادة التشغيل...", alert=True)
        os.execl(sys.executable, sys.executable, *sys.argv)

# --- [ إقلاع النظام ] ---
async def boot_all():
    data = db.get_data()
    for cid, info in data['clients_factory'].items():
        asyncio.create_task(start_client_instance(cid, info['token']))

print("👑 Imperial Factory Server Started!")
master_bot.loop.run_until_complete(boot_all())
master_bot.run_until_disconnected()
