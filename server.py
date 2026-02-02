# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE ULTIMATE IMPERIAL FACTORY - OVER 500 LINES 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- المطور الرئيسي: 8504553407
- نظام التحكم: Master Bot -> Multi-Client Bots
- المميزات: (تحديد أيام الترخيص، حد أرقام صارم، منع تنصيب للغير)
- طرق التجميع: (محرك الإحالة الذكي، محرك الهدية اليومية Bypass)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os, sys, json, asyncio, datetime, random, logging, re, time
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import *

# --- [ الإعدادات الجوهرية ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
BOT_TOKEN = "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY" 
MASTER_ID = 8504553407
DB_PATH = "imperial_ultimate_v3.json"

# --- [ إعدادات السجلات ] ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("ImperialEngine")

# --- [ محرك إدارة البيانات ] ---
class ImperialDatabase:
    @staticmethod
    def load():
        if not os.path.exists(DB_PATH):
            data = {
                "master": MASTER_ID,
                "clients": {}, # { "id": { "token": "", "expiry": "", "limit": 0, "accs": {} } }
                "config": {"target": "@t06bot", "ref": "", "delay": 45},
                "logs": []
            }
            with open(DB_PATH, 'w') as f: json.dump(data, f, indent=4)
        return json.load(open(DB_PATH, 'r'))

    @staticmethod
    def save(data):
        with open(DB_PATH, 'w') as f: json.dump(data, f, indent=4)

# --- [ 🛠️ محركات التجميع الاحترافية 🛠️ ] ---

# 1. محرك الإحالة (Referral Engine)
async def engine_referral(client, ref_link, log_queue):
    try:
        if not ref_link: return False
        bot_u = ref_link.split("/")[-1].split("?")[0]
        param = ref_link.split("start=")[-1]
        await client(functions.messages.StartBotRequest(bot=bot_u, peer=bot_u, start_param=param))
        log_queue.append(f"🔗 [REFERRAL] Success for: {bot_u}")
        return True
    except Exception as e:
        log_queue.append(f"⚠️ [REFERRAL] Error: {str(e)[:30]}")
        return False

# 2. محرك الهدية اليومية (Daily Gift Engine with Bypass)
async def engine_daily_gift(client, target, log_queue):
    try:
        await client.send_message(target, "/start")
        await asyncio.sleep(5)
        
        for _ in range(12): # محاولات تخطي الاشتراك الإجباري
            msgs = await client.get_messages(target, limit=1)
            if not msgs or not msgs[0].reply_markup: break
            
            action = False
            for row in msgs[0].reply_markup.rows:
                for btn in row.buttons:
                    # تخطي القنوات
                    if isinstance(btn, types.KeyboardButtonUrl):
                        try:
                            ch = btn.url.split('/')[-1]
                            await client(functions.channels.JoinChannelRequest(channel=ch))
                            log_queue.append(f"✅ [BYPASS] Joined: {ch}")
                            action = True
                        except: pass
                    # أزرار التحقق
                    elif any(x in btn.text for x in ["تحقق", "تم", "تأكيد", "Verify"]):
                        await msgs[0].click(text=btn.text)
                        await asyncio.sleep(3)
                        action = True
                    # زر الهدية النهائي
                    elif any(x in btn.text for x in ["هدية", "يومية", "Daily", "Gift"]):
                        await msgs[0].click(text=btn.text)
                        log_queue.append(f"💎 [GIFT] Points Collected!")
                        return True
            if not action: break
        return False
    except Exception as e:
        log_queue.append(f"❌ [GIFT] Failed: {str(e)[:30]}")
        return False

# --- [ 🤖 محرك تشغيل بوتات الزبائن (Multi-Instance) 🤖 ] ---
async def start_client_bot(c_id, c_token):
    try:
        sub_bot = TelegramClient(f"sub_bot_{c_id}", API_ID, API_HASH)
        await sub_bot.start(bot_token=c_token)
        
        @sub_bot.on(events.NewMessage(pattern='/start'))
        async def sub_start(event):
            if event.sender_id != int(c_id): return
            db = ImperialDatabase.load()
            info = db['clients'].get(str(c_id))
            if not info: return
            
            # فحص مدة الترخيص
            exp_date = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
            if datetime.datetime.now() > exp_date:
                return await event.reply("⚠️ انتهت مدة الترخيص! يرجى التواصل مع المطور للتجديد.")

            text = (f"💎 **مرحباً بك في نسختك الإمبراطورية** 💎\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏳ ينتهي الترخيص: `{info['expiry']}`\n"
                    f"🔢 حد الأرقام: `{len(info['accs'])} / {info['limit']}`\n"
                    f"🎯 الهدف الحالي: `{db['config']['target']}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━")
            btns = [
                [Button.inline("➕ إضافة حساب جديد", "add_acc"), Button.inline("🗑️ مسح حساب", "del_acc")],
                [Button.inline("🚀 بدء التجميع (إحالة)", "farm_ref"), Button.inline("🎁 بدء التجميع (هدية)", "farm_gift")],
                [Button.inline("🔄 تجميع (الكل معاً)", "farm_all")],
                [Button.inline("📊 عرض حساباتي", "list_accs")],
                [Button.url("🧑‍💻 المطور", "https://t.me/Tele_Sajad")]
            ]
            await event.reply(text, buttons=btns)

        @sub_bot.on(events.CallbackQuery)
        async def sub_actions(event):
            db = ImperialDatabase.load()
            cid = str(event.sender_id)
            if cid not in db['clients']: return
            cmd = event.data.decode()

            if cmd == "add_acc":
                if len(db['clients'][cid]['accs']) >= db['clients'][cid]['limit']:
                    return await event.answer("❌ وصلت للحد الأقصى المسموح لك!", alert=True)
                async with sub_bot.conversation(event.sender_id) as conv:
                    await conv.send_message("🔑 أرسل الـ String Session الآن:"); ss = (await conv.get_response()).text.strip()
                    await conv.send_message("📱 أرسل رقم الهاتف:"); ph = (await conv.get_response()).text.strip()
                    db['clients'][cid]['accs'][ph] = ss
                    ImperialDatabase.save(db); await conv.send_message("✅ تم ربط الحساب بنجاح.")

            elif cmd == "del_acc":
                async with sub_bot.conversation(event.sender_id) as conv:
                    await conv.send_message("🗑️ أرسل الرقم لمسحه:"); ph = (await conv.get_response()).text.strip()
                    if ph in db['clients'][cid]['accs']:
                        del db['clients'][cid]['accs'][ph]
                        ImperialDatabase.save(db); await conv.send_message("✅ تم الحذف.")
                    else: await conv.send_message("❌ الرقم غير موجود.")

            elif cmd.startswith("farm_"):
                mode = cmd.split("_")[-1]
                await event.answer("🚀 بدأ التجميع...", alert=False)
                for ph, ss in db['clients'][cid]['accs'].items():
                    cl = TelegramClient(StringSession(ss), API_ID, API_HASH)
                    await cl.connect()
                    if mode in ["ref", "all"]: await engine_referral(cl, db['config']['ref'], db['logs'])
                    if mode in ["gift", "all"]: await engine_daily_gift(cl, db['config']['target'], db['logs'])
                    await cl.disconnect(); await asyncio.sleep(2)
                await event.respond("🏁 انتهى التجميع لجميع حساباتك.")

            elif cmd == "list_accs":
                accs = db['clients'][cid]['accs']
                msg = "📊 **أرقامك المربوطة:**\n\n" + "\n".join([f"📱 `{p}`" for p in accs]) if accs else "لا توجد أرقام."
                await event.respond(msg)

        await sub_bot.run_until_disconnected()
    except: pass

# --- [ 👑 البوت الماستر (المصنع الرئيسي) 👑 ] ---
master_bot = TelegramClient("Imperial_Master", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@master_bot.on(events.NewMessage(pattern='/start'))
async def master_ui(event):
    if event.sender_id != MASTER_ID: return
    db = ImperialDatabase.load()
    text = (f"👑 **لوحة تحكم المصنع الإمبراطوري** 👑\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 عدد الزبائن: `{len(db['clients'])}` \n"
            f"⚙️ الهدف: `{db['config']['target']}`\n"
            f"🔗 الإحالة: `{db['config']['ref'][:20]}...`")
    btns = [
        [Button.inline("💎 تنصيب لزبون جديد", "m_deploy")],
        [Button.inline("📊 عرض الزبائن", "m_view"), Button.inline("🗑️ حذف زبون", "m_kick")],
        [Button.inline("⚙️ إعدادات التجميع", "m_config")],
        [Button.inline("📝 السجل العام", "m_logs"), Button.inline("📩 أداة الاستخراج", "m_tool")]
    ]
    await event.reply(text, buttons=btns)

@master_bot.on(events.CallbackQuery)
async def master_handler(event):
    if event.sender_id != MASTER_ID: return
    db = ImperialDatabase.load()
    cmd = event.data.decode()

    if cmd == "m_deploy":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("👤 أرسل ID الزبون:"); cid = (await conv.get_response()).text.strip()
            await conv.send_message("🔑 أرسل توكن بوت الزبون:"); ctok = (await conv.get_response()).text.strip()
            await conv.send_message("⏳ مدة الترخيص (أيام):"); cday = (await conv.get_response()).text.strip()
            await conv.send_message("🔢 حد الأرقام المسموح له:"); clim = (await conv.get_response()).text.strip()
            
            exp = (datetime.datetime.now() + datetime.timedelta(days=int(cday))).strftime('%Y-%m-%d')
            db['clients'][cid] = {"token": ctok, "expiry": exp, "limit": int(clim), "accs": {}}
            ImperialDatabase.save(db)
            
            asyncio.create_task(start_client_bot(cid, ctok))
            await conv.send_message(f"✅ تم تنصيب بوت الزبون {cid} بنجاح!")

    elif cmd == "m_config":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🎯 يوزر الهدف:"); db['config']['target'] = (await conv.get_response()).text.strip()
            await conv.send_message("🔗 رابط الإحالة:"); db['config']['ref'] = (await conv.get_response()).text.strip()
            ImperialDatabase.save(db); await conv.send_message("✅ تم التحديث.")

    elif cmd == "m_view":
        msg = "📊 **الزبائن:**\n"
        for k, v in db['clients'].items(): msg += f"👤 `{k}` | 📅 `{v['expiry']}` | 🔢 `{v['limit']}`\n"
        await event.respond(msg or "لا يوجد زبائن.")

    elif cmd == "m_tool":
        code = f"from telethon import TelegramClient\nimport asyncio\nasync def x():\n async with TelegramClient(None, {API_ID}, '{API_HASH}') as c: print(c.session.save())\nasyncio.run(x())"
        with open("GetSession.py", "w") as f: f.write(code)
        await event.respond("🛠 أداة الاستخراج للزبائن:", file="GetSession.py")

async def boot_all():
    db = ImperialDatabase.load()
    for cid, info in db['clients'].items():
        asyncio.create_task(start_client_bot(cid, info['token']))

print("👑 Factory Server is Running...")
master_bot.loop.run_until_complete(boot_all())
master_bot.run_until_disconnected()
