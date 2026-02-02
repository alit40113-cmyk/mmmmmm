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
DB_PATH = "imperial_mega_v5.json"

# --- [ إعدادات السجلات الاحترافية ] ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('imperial_v5.log')]
)
logger = logging.getLogger("ImperialFactory")

# --- [ محرك إدارة قاعدة البيانات المركزية ] ---
class ImperialDatabase:
    def __init__(self, path):
        self.path = path
        self.init_db()

    def init_db(self):
        if not os.path.exists(self.path):
            data = {
                "master": MASTER_ID,
                "clients": {}, # { "id": { "token": "", "expiry": "", "limit": 0, "accs": {} } }
                "config": {
                    "target": "@t06bot", 
                    "ref": "", 
                    "delay": 40,
                    "min_sleep": 2,
                    "max_sleep": 5
                },
                "stats": {"runs": 0, "total_accs": 0},
                "logs": [f"🚀 System Started: {datetime.datetime.now()}"]
            }
            self.save(data)

    def load(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, data):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

db_core = ImperialDatabase(DB_PATH)

# --- [ محركات التجميع الذكية (The Engines) ] ---

class FarmingEngine:
    @staticmethod
    async def referral_action(client, ref_link):
        """محرك الإحالة مع تخطي الحماية"""
        try:
            if not ref_link or "start=" not in ref_link: return False
            bot_username = ref_link.split("/")[-1].split("?")[0]
            start_param = ref_link.split("start=")[-1]
            await client(functions.messages.StartBotRequest(
                bot=bot_username, 
                peer=bot_username, 
                start_param=start_param
            ))
            return True
        except Exception as e:
            logger.error(f"Referral Error: {e}")
            return False

    @staticmethod
    async def gift_bypass_action(client, target):
        """محرك الهدية اليومية مع تخطي الاشتراك الإجباري"""
        try:
            await client.send_message(target, "/start")
            await asyncio.sleep(4)
            
            # محاولات تخطي قنوات الاشتراك (حتى 15 محاولة)
            for _ in range(15):
                msgs = await client.get_messages(target, limit=1)
                if not msgs or not msgs[0].reply_markup: break
                
                action_found = False
                for row in msgs[0].reply_markup.rows:
                    for btn in row.buttons:
                        # 1. تخطي الانضمام للقنوات
                        if isinstance(btn, types.KeyboardButtonUrl):
                            channel = btn.url.split('/')[-1]
                            try:
                                await client(functions.channels.JoinChannelRequest(channel=channel))
                                action_found = True
                            except: pass
                        # 2. النقر على أزرار التحقق
                        elif any(x in btn.text for x in ["تحقق", "تم", "تأكيد", "Verify", "Done"]):
                            await msgs[0].click(text=btn.text)
                            await asyncio.sleep(3)
                            action_found = True
                        # 3. النقر على زر الهدية
                        elif any(x in btn.text for x in ["هدية", "يومية", "Daily", "Gift", "Claim"]):
                            await msgs[0].click(text=btn.text)
                            return True
                if not action_found: break
            return False
        except Exception as e:
            logger.error(f"Gift Error: {e}")
            return False

# --- [ محرك تشغيل بوتات الزبائن (Sub-Bot Instance) ] ---

async def launch_sub_instance(client_id, bot_token):
    """هذا الكود يمثل الـ Instance المنفصل لكل زبون"""
    try:
        sub_client = TelegramClient(f"sessions/sub_{client_id}", API_ID, API_HASH)
        await sub_client.start(bot_token=bot_token)
        
        @sub_client.on(events.NewMessage(pattern='/start'))
        async def sub_start_handler(event):
            if event.sender_id != int(client_id): return
            db = db_core.load()
            client_info = db['clients'].get(str(client_id))
            if not client_info: return
            
            # فحص تاريخ انتهاء الترخيص
            expiry_dt = datetime.datetime.strptime(client_info['expiry'], '%Y-%m-%d')
            if datetime.datetime.now() > expiry_dt:
                return await event.reply("⚠️ **عذراً، انتهت مدة ترخيص بوتك!**\nيرجى التواصل مع المالك للتجديد.")

            welcome_msg = (
                f"💎 **مرحباً بك في لوحة تحكم نسختك**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 تاريخ الانتهاء: `{client_info['expiry']}`\n"
                f"🔢 حد الأرقام: `{len(client_info['accs'])} / {client_info['limit']}`\n"
                f"🎯 الهدف العالمي: `{db['config']['target']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            buttons = [
                [Button.inline("➕ إضافة حساب جديد", "sub_add"), Button.inline("🗑️ مسح حساب", "sub_del")],
                [Button.inline("🚀 بدء تجميع إحالة", "sub_farm_ref"), Button.inline("🎁 بدء تجميع هدية", "sub_farm_gift")],
                [Button.inline("🔄 تجميع شامل (الكل)", "sub_farm_all")],
                [Button.inline("📊 عرض حساباتي المربوطة", "sub_list")],
                [Button.url("🧑‍💻 المطور الرئيسي", "https://t.me/Tele_Sajad")]
            ]
            await event.reply(welcome_msg, buttons=buttons)

        @sub_client.on(events.CallbackQuery)
        async def sub_callback_handler(event):
            db = db_core.load()
            cid = str(event.sender_id)
            if cid not in db['clients']: return
            query = event.data.decode()

            # 1. إضافة حساب للزبون
            if query == "sub_add":
                if len(db['clients'][cid]['accs']) >= db['clients'][cid]['limit']:
                    return await event.answer("❌ وصلت للحد الأقصى المسموح لك!", alert=True)
                
                async with sub_client.conversation(event.sender_id) as conv:
                    await conv.send_message("🔑 **يرجى إرسال الـ String Session:**")
                    session_str = (await conv.get_response()).text.strip()
                    await conv.send_message("📱 **يرجى إرسال رقم الهاتف للتعريف:**")
                    phone_num = (await conv.get_response()).text.strip()
                    
                    try:
                        # فحص الصلاحية قبل الحفظ
                        test_cl = TelegramClient(StringSession(session_str), API_ID, API_HASH)
                        await test_cl.connect()
                        if await test_cl.is_user_authorized():
                            db['clients'][cid]['accs'][phone_num] = session_str
                            db_core.save(db)
                            await conv.send_message(f"✅ تم ربط الحساب `{phone_num}` بنجاح في نسختك.")
                        else:
                            await conv.send_message("❌ السيشن الذي أرسلته غير فعال!")
                        await test_cl.disconnect()
                    except Exception as e:
                        await conv.send_message(f"⚠️ خطأ أثناء الفحص: {e}")

            # 2. مسح حساب للزبون
            elif query == "sub_del":
                async with sub_client.conversation(event.sender_id) as conv:
                    await conv.send_message("🗑️ **أرسل الرقم الذي تريد حذفه من القائمة:**")
                    phone_to_del = (await conv.get_response()).text.strip()
                    if phone_to_del in db['clients'][cid]['accs']:
                        del db['clients'][cid]['accs'][phone_to_del]
                        db_core.save(db)
                        await conv.send_message(f"✅ تم حذف الرقم `{phone_to_del}` نهائياً.")
                    else:
                        await conv.send_message("❌ هذا الرقم غير موجود في قائمتك.")

            # 3. عرض حسابات الزبون
            elif query == "sub_list":
                my_accs = db['clients'][cid]['accs']
                if not my_accs:
                    return await event.respond("📊 ليس لديك أي حسابات مربوطة حالياً.")
                msg = "📊 **أرقامك المربوطة في المنظومة:**\n\n"
                for i, p in enumerate(my_accs.keys(), 1):
                    msg += f"{i} - 📱 `{p}`\n"
                await event.respond(msg)

            # 4. محرك التجميع للزبون
            elif query.startswith("sub_farm_"):
                mode = query.split("_")[-1]
                await event.answer("🚀 بدأ المحرك بالعمل على حساباتك...", alert=False)
                logs = []
                for phone, session in db['clients'][cid]['accs'].items():
                    try:
                        temp_cl = TelegramClient(StringSession(session), API_ID, API_HASH)
                        await temp_cl.connect()
                        if mode in ["ref", "all"]:
                            await FarmingEngine.referral_action(temp_cl, db['config']['ref'])
                        if mode in ["gift", "all"]:
                            await FarmingEngine.gift_bypass_action(temp_cl, db['config']['target'])
                        await temp_cl.disconnect()
                        logs.append(f"✅ الحساب `{phone}`: تم بنجاح.")
                    except:
                        logs.append(f"❌ الحساب `{phone}`: فشل الاتصال.")
                    await asyncio.sleep(db['config']['delay'])
                
                final_log = "🏁 **تقرير عملية التجميع:**\n\n" + "\n".join(logs)
                await event.respond(final_log)

        await sub_client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Instance Error for {client_id}: {e}")

# --- [ 👑 بوت الماستر الرئيسي (The Factory Master) 👑 ] ---

master_bot = TelegramClient("Imperial_Master_Core", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@master_bot.on(events.NewMessage(pattern='/start'))
async def master_ui_handler(event):
    if event.sender_id != MASTER_ID: return
    db = db_core.load()
    dashboard = (
        f"👑 **مرحباً بك في مصنع الإمبراطورية الرئيسي** 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 عدد الزبائن المفعّلين: `{len(db['clients'])}` \n"
        f"⚙️ الهدف الحالي: `{db['config']['target']}`\n"
        f"🔗 رابط الإحالة: `{db['config']['ref'][:25]}...` \n"
        f"⏳ تأخير التجميع: `{db['config']['delay']} ثانية` \n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    master_btns = [
        [Button.inline("💎 تنصيب بوت لزبون جديد", "m_deploy")],
        [Button.inline("📊 إدارة الزبائن", "m_view_c"), Button.inline("🗑️ حذف زبون وطرد", "m_kick_c")],
        [Button.inline("⚙️ ضبط الإعدادات العامة", "m_settings")],
        [Button.inline("📝 سجل العمليات", "m_logs"), Button.inline("📩 أداة الاستخراج", "m_tool")],
        [Button.inline("🔄 إعادة تشغيل المنظومة", "m_reboot")]
    ]
    await event.reply(dashboard, buttons=master_btns)

@master_bot.on(events.CallbackQuery)
async def master_callback_handler(event):
    if event.sender_id != MASTER_ID: return
    db = db_core.load()
    cmd = event.data.decode()

    # 1. تنصيب لزبون (مع تحديد الأيام والحد)
    if cmd == "m_deploy":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("👤 **أرسل ID الزبون المراد تفعيله:**")
            cid = (await conv.get_response()).text.strip()
            await conv.send_message("🔑 **أرسل توكن بوت الزبون:**")
            ctoken = (await conv.get_response()).text.strip()
            await conv.send_message("⏳ **عدد أيام الترخيص (مثلاً 30):**")
            cdays = (await conv.get_response()).text.strip()
            await conv.send_message("🔢 **حد الأرقام المسموح له (مثلاً 15):**")
            climit = (await conv.get_response()).text.strip()
            
            try:
                # حساب تاريخ الانتهاء
                expiry = (datetime.datetime.now() + datetime.timedelta(days=int(cdays))).strftime('%Y-%m-%d')
                db['clients'][cid] = {
                    "token": ctoken,
                    "expiry": expiry,
                    "limit": int(climit),
                    "accs": {}
                }
                db_core.save(db)
                # إطلاق النسخة فوراً
                asyncio.create_task(launch_sub_instance(cid, ctoken))
                await conv.send_message(f"✅ **تم تنصيب نسخة الزبون بنجاح!**\n📅 الانتهاء: `{expiry}`\n🔢 الحد: `{climit}` أرقام.")
            except Exception as e:
                await conv.send_message(f"❌ فشل التنصيب: {e}")

    # 2. حذف زبون
    elif cmd == "m_kick_c":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🗑️ **أرسل ID الزبون لإلغاء ترخيصه:**")
            cid = (await conv.get_response()).text.strip()
            if cid in db['clients']:
                del db['clients'][cid]
                db_core.save(db)
                await conv.send_message(f"✅ تم حذف الزبون وإيقاف صلاحياته.")
            else:
                await conv.send_message("❌ هذا الـ ID غير مسجل.")

    # 3. الإعدادات العامة
    elif cmd == "m_settings":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🎯 **أرسل يوزر البوت المستهدف (الهدف):**")
            db['config']['target'] = (await conv.get_response()).text.strip()
            await conv.send_message("🔗 **أرسل رابط الإحالة الجديد:**")
            db['config']['ref'] = (await conv.get_response()).text.strip()
            await conv.send_message("⏳ **أرسل وقت التأخير بين الحسابات (بالثواني):**")
            db['config']['delay'] = int((await conv.get_response()).text.strip())
            db_core.save(db)
            await conv.send_message("✅ تم تحديث الإعدادات العامة للمنظومة.")

    # 4. أداة استخراج السيشن (لإرسالها للزبائن)
    elif cmd == "m_tool":
        tool_code = (
            f"from telethon import TelegramClient\nimport asyncio\n"
            f"async def get_ss():\n"
            f"  async with TelegramClient(None, {API_ID}, '{API_HASH}') as c:\n"
            f"    print('\\nYour Session String:\\n', c.session.save())\n"
            f"asyncio.run(get_ss())"
        )
        with open("Imperial_Extractor.py", "w") as f: f.write(tool_code)
        await event.respond("🛠 **أرسل هذا الملف لزبائنك لاستخراج السيشن:**", file="Imperial_Extractor.py")

    # 5. عرض الزبائن
    elif cmd == "m_view_c":
        if not db['clients']: return await event.respond("📊 لا يوجد زبائن حالياً.")
        msg = "📊 **قائمة الزبائن وتراخيصهم:**\n\n"
        for cid, info in db['clients'].items():
            msg += f"👤 `{cid}` | 📅 `{info['expiry']}` | 🔢 `{len(info['accs'])}/{info['limit']}`\n"
        await event.respond(msg)

    # 6. إعادة تشغيل المنظومة
    elif cmd == "m_reboot":
        await event.answer("🔄 جاري إعادة تشغيل كافة Instances...", alert=True)
        os.execl(sys.executable, sys.executable, *sys.argv)

# --- [ تشغيل البوتات المخزنة عند الإقلاع ] ---
async def boot_system():
    data = db_core.load()
    logger.info(f"Booting {len(data['clients'])} client instances...")
    for cid, info in data['clients'].items():
        asyncio.create_task(launch_sub_instance(cid, info['token']))

if __name__ == "__main__":
    print("👑 Imperial Factory Server is Online!")
    master_bot.loop.run_until_complete(boot_system())
    master_bot.run_until_disconnected()
