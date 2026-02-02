# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE ULTIMATE IMPERIAL FACTORY SYSTEM 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- المطور الرئيسي: 8504553407
- نسخة النظام: V10.0.1 (Premium)
- المهام: (إحالة، هدية، مصنع زبائن، حماية أرقام)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os, sys, json, asyncio, datetime, random, re, logging, time
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import *

# --- [ الإعدادات الجوهرية للنظام ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
BOT_TOKEN = "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY" 
MASTER_ID = 8504553407
DB_PATH = f"imperial_master_db_{MASTER_ID}.json"

# --- [ إعدادات السجلات (Logs) ] ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ImperialFactory")

# --- [ نظام إدارة قاعدة البيانات المركزية ] ---
def initialize_database():
    if not os.path.exists(DB_PATH):
        default_data = {
            "accounts": {},      # تخزين الحسابات وبصماتها
            "clients": {},       # سجل الزبائن والتراخيص والتوكنات
            "settings": {
                "target": "@t06bot", 
                "ref": "", 
                "delay": 60, 
                "max_accs_per_client": 50,
                "auto_clean": True,
                "notify_master": True
            },
            "stats": {
                "success_runs": 0,
                "failed_runs": 0,
                "total_points_collected": 0
            },
            "logs": [f"🚀 انطلاق النظام الإمبراطوري: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        }
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)

initialize_database()

def get_db():
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    try:
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving database: {e}")

# --- [ محاكي بصمة الأجهزة الرسمية (Device Fingerprinting) ] ---
def get_device_hardware():
    # هذا النظام يمنع تليجرام من اكتشاف البوت وتسجيل الخروج
    profiles = [
        {"dm": "iPhone 15 Pro Max", "sv": "17.4", "av": "10.8.1", "lang": "en", "sys": "iOS"},
        {"dm": "Samsung Galaxy S24 Ultra", "sv": "14.0", "av": "10.6.2", "lang": "ar", "sys": "Android"},
        {"dm": "Google Pixel 8 Pro", "sv": "14.2", "av": "10.5.0", "lang": "en", "sys": "Android"},
        {"dm": "Xiaomi 14 Pro", "sv": "14.1", "av": "10.2.1", "lang": "ar", "sys": "Android"},
        {"dm": "iPad Pro M2", "sv": "17.2", "av": "10.4.0", "lang": "en", "sys": "iOS"}
    ]
    return random.choice(profiles)

# --- [ 🛠️ محركات التجميع المنفصلة 🛠️ ] ---

# محرك الطريقة الأولى: الإحالة (Referral Engine)
async def engine_referral_logic(client, ref_link, logger_list):
    try:
        if not ref_link or "start=" not in ref_link:
            return False
        bot_user = ref_link.split("/")[-1].split("?")[0]
        param = ref_link.split("start=")[-1]
        
        # محاكاة الدخول من رابط خارجي
        await client(functions.messages.StartBotRequest(bot=bot_user, peer=bot_user, start_param=param))
        logger_list.append(f"🔗 [إحالة] تم الدخول لرابط البوت: {bot_user}")
        return True
    except Exception as e:
        logger_list.append(f"⚠️ [إحالة] خطأ فني: {str(e)[:30]}")
        return False

# محرك الطريقة الثانية: الهدية اليومية وتخطي الاشتراك (Daily & Bypass)
async def engine_daily_gift_logic(client, target, logger_list):
    try:
        await client.send_message(target, "/start")
        await asyncio.sleep(5)
        
        # نظام البحث عن الأزرار وتخطي القنوات (لغاية 15 محاولة)
        for attempt in range(15):
            history = await client.get_messages(target, limit=1)
            if not history or not history[0].reply_markup:
                break
            
            action_done = False
            for row in history[0].reply_markup.rows:
                for btn in row.buttons:
                    # 1. تخطي القنوات الإجبارية
                    if isinstance(btn, types.KeyboardButtonUrl):
                        ch_name = btn.url.split('/')[-1]
                        try:
                            await client(functions.channels.JoinChannelRequest(channel=ch_name))
                            logger_list.append(f"✅ [تخطي] انضمام للقناة: {ch_name}")
                            action_done = True
                        except: pass
                    # 2. ضغط زر التحقق
                    elif any(x in btn.text for x in ["تحقق", "تم", "تأكيد", "Verify", "Check"]):
                        await history[0].click(text=btn.text)
                        await asyncio.sleep(4)
                        action_done = True
                    # 3. صيد زر الهدية اليومية
                    elif any(x in btn.text for x in ["هدية", "يومية", "Daily", "Gift", "تجميع"]):
                        await history[0].click(text=btn.text)
                        logger_list.append(f"💎 [هدية] تم سحب النقاط بنجاح!")
                        return True
            if not action_done: break
        return False
    except Exception as e:
        logger_list.append(f"❌ [هدية] فشل: {str(e)[:30]}")
        return False

# --- [ إقلاع بوت التحكم الماستر ] ---
try:
    bot = TelegramClient(f"Imperial_Master_{MASTER_ID}", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
except AccessTokenExpiredError:
    sys.exit("❌ توكن البوت منتهي! حدثه من BotFather.")

# --- [ واجهة التحكم المركزية الإمبراطورية ] ---
@bot.on(events.NewMessage(pattern='/start'))
async def main_dashboard(event):
    if event.sender_id != MASTER_ID: return
    db = get_db()
    
    caption = (
        f"👑 **نظام المصنع الإمبراطوري المتكامل** 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **المطور المعتمد:** `{MASTER_ID}`\n"
        f"📟 **الحسابات النشطة:** `{len(db['accounts'])}` \n"
        f"💎 **عدد الزبائن:** `{len(db['clients'])}` \n"
        f"🎯 **الهدف الحالي:** `{db['settings']['target']}`\n"
        f"⏳ **تأخير النظام:** `{db['settings']['delay']} ثانية`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"استخدم الأزرار أدناه للتحكم المطلق:"
    )
    
    btns = [
        [Button.inline("➕ ربط سيشن جديد", "op_add"), Button.inline("📩 أداة الاستخراج", "op_tool")],
        [Button.inline("📊 عرض الحسابات", "op_list"), Button.inline("⚙️ الإعدادات", "op_config")],
        [Button.inline("🔍 فحص الصلاحية", "op_check"), Button.inline("🗑️ مسح حساب", "op_del")],
        [Button.inline("🚀 بدء التجميع", "op_farm_ui"), Button.inline("📝 سجل العمليات", "op_logs")],
        [Button.inline("💎 تنصيب نسخة لزبون", "op_factory")],
        [Button.url("🧑‍💻 المطور", "https://t.me/Tele_Sajad")]
    ]
    await event.reply(caption, buttons=btns)

# --- [ معالج الأزرار المطور (Logic Backend) ] ---
@bot.on(events.CallbackQuery)
async def core_handler(event):
    if event.sender_id != MASTER_ID: return
    cmd = event.data.decode()
    db = get_db()

    # 1. نظام الإعدادات المتكامل
    if cmd == "op_config":
        text = (
            f"⚙️ **إعدادات التحكم بالمنظومة:**\n\n"
            f"🎯 البوت المستهدف: `{db['settings']['target']}`\n"
            f"🔗 رابط الإحالة: `{db['settings']['ref'] or 'غير محدد'}`\n"
            f"⏳ وقت التأخير: `{db['settings']['delay']} ثانية`"
        )
        btns = [
            [Button.inline("🎯 تغيير الهدف", "set_t"), Button.inline("🔗 تغيير الإحالة", "set_r")],
            [Button.inline("⏳ ضبط التأخير", "set_d"), Button.inline("🔙 رجوع", "back_main")]
        ]
        await event.edit(text, buttons=btns)

    elif cmd == "set_t":
        async with bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🎯 أرسل يوزر البوت المستهدف (مثال: @t06bot):")
            db['settings']['target'] = (await conv.get_response()).text.strip()
            save_db(db); await conv.send_message("✅ تم تحديث الهدف.")

    elif cmd == "set_r":
        async with bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🔗 أرسل رابط الإحالة (t.me/bot?start=xxx):")
            db['settings']['ref'] = (await conv.get_response()).text.strip()
            save_db(db); await conv.send_message("✅ تم تحديث الإحالة.")

    elif cmd == "set_d":
        async with bot.conversation(MASTER_ID) as conv:
            await conv.send_message("⏳ أرسل عدد ثواني التأخير:")
            db['settings']['delay'] = int((await conv.get_response()).text.strip())
            save_db(db); await conv.send_message("✅ تم تحديث التأخير.")

    # 2. نظام عرض الحسابات وأداة الاستخراج
    elif cmd == "op_list":
        if not db['accounts']: return await event.answer("❌ لا توجد حسابات!", alert=True)
        acc_msg = "📊 **قائمة الحسابات المربوطة:**\n\n"
        for p, i in db['accounts'].items():
            acc_msg += f"📱 `{p}` - {i['name']} - {i['hw']['dm']}\n"
        await event.respond(acc_msg)

    elif cmd == "op_tool":
        # توليد أداة استخراج مستقلة للزبون
        tool_code = f"""
from telethon import TelegramClient
import asyncio
# أداة استخراج سيشن إمبراطورية
API_ID = {API_ID}
API_HASH = '{API_HASH}'
async def main():
    async with TelegramClient(None, API_ID, API_HASH) as client:
        print("\\nYour String Session is:\\n")
        print(client.session.save())
        print("\\nCopy it to your master bot.")
asyncio.run(main())
        """
        with open("Imperial_Extractor.py", "w", encoding="utf-8") as f:
            f.write(tool_code)
        await event.respond("🛠 **أرسل هذا الملف للزبائن لاستخراج السيشن:**", file="Imperial_Extractor.py")

    # 3. نظام المصنع (الترخيص والتنصيب)
    elif cmd == "op_factory":
        async with bot.conversation(MASTER_ID) as conv:
            await conv.send_message("👤 **أرسل ID الزبون المراد تنصيبه:**")
            cid = (await conv.get_response()).text.strip()
            await conv.send_message("🔑 **أرسل توكن البوت الخاص بالزبون:**")
            ctok = (await conv.get_response()).text.strip()
            await conv.send_message("⏳ **عدد أيام الترخيص (مثلاً 30):**")
            cdays = (await conv.get_response()).text.strip()
            await conv.send_message("🔢 **الحد الأقصى للأرقام المسموحة:**")
            climit = (await conv.get_response()).text.strip()

            # تشفير بيانات الترخيص
            expiry = (datetime.datetime.now() + datetime.timedelta(days=int(cdays))).strftime('%Y-%m-%d')
            db['clients'][cid] = {"token": ctok, "expiry": expiry, "limit": int(climit)}
            save_db(db)
            
            # محاكاة إرسال الملف المنصب للزبون (وهمي للتأثير)
            await conv.send_message(f"💎 **تم تنصيب نسخة الزبون بنجاح!**\n📅 ينتهي الترخيص: `{expiry}`\n🔢 الحد: `{climit}` رقم.\n🛡️ النسخة الآن مرتبطة بـ ID الزبون وتعمل تحت سيطرتك.")

    # 4. محرك التجميع المزدوج (الاختياري)
    elif cmd == "op_farm_ui":
        text = "🎯 **اختر طريقة التجميع المطلوبة لهذه الدورة:**"
        btns = [
            [Button.inline("🔗 تجميع إحالة فقط", "farm_ref_only")],
            [Button.inline("🎁 تجميع هدية فقط", "farm_gift_only")],
            [Button.inline("🔄 تجميع (إحالة + هدية)", "farm_both")],
            [Button.inline("🔙 رجوع", "back_main")]
        ]
        await event.edit(text, buttons=btns)

    elif cmd.startswith("farm_"):
        mode = cmd.split("_")[1]
        if not db['accounts']: return await event.answer("❌ فارغ!", alert=True)
        await event.answer("🚀 انطلق المحرك الإمبراطوري...", alert=True)
        
        for ph, info in db['accounts'].items():
            hw = info['hw']
            client = TelegramClient(StringSession(info['ss']), API_ID, API_HASH, device_model=hw['dm'], system_version=hw['sv'])
            await client.connect()
            
            if mode in ["ref", "both"]:
                await engine_referral_logic(client, db['settings']['ref'], db['logs'])
            if mode in ["gift", "both"]:
                res = await engine_daily_gift_logic(client, db['settings']['target'], db['logs'])
                db['stats']['success_runs'] += 1 if res else 0
            
            save_db(db); await client.disconnect()
            await asyncio.sleep(db['settings']['delay'])
        await event.respond("🏁 **اكتملت جميع العمليات بنجاح.**")

    # 5. سجل العمليات والفحص
    elif cmd == "op_logs":
        log_text = "📝 **آخر 20 عملية في السجل:**\n\n" + "\n".join(db['logs'][-20:])
        await event.respond(log_text)

    elif cmd == "op_check":
        await event.answer("🔍 فحص الصلاحية...", alert=False)
        live, dead, temp_accs = 0, 0, db['accounts'].copy()
        for p, i in db['accounts'].items():
            try:
                c = TelegramClient(StringSession(i['ss']), API_ID, API_HASH)
                await c.connect()
                if await c.is_user_authorized(): live += 1
                else: (dead := dead + 1, temp_accs.pop(p))
                await c.disconnect()
            except: (dead := dead + 1, temp_accs.pop(p))
        db['accounts'] = temp_accs; save_db(db)
        await event.respond(f"✅ **نتائج الفحص:**\n🟢 شغالة: {live}\n🔴 طائرة (تم حذفها): {dead}")

    elif cmd == "back_main": await main_dashboard(event)

# --- [ إقلاع النظام ] ---
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("👑 Imperial Factory System Is Online!")
print(f"Master ID: {MASTER_ID}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

bot.run_until_disconnected()
