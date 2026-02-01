# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import asyncio
import logging
import datetime
import subprocess
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PasswordHashInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError
)

# --- [ إعدادات نظام السجلات - Logging ] ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- [ الثوابت وإعدادات الهوية ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

# التحقق من بارامترات التشغيل
if len(sys.argv) > 2:
    CURRENT_TOKEN = sys.argv[1]
    CURRENT_MASTER = int(sys.argv[2])
    IS_SUB_BOT = True
else:
    # البيانات الافتراضية للمالك الأساسي
    CURRENT_MASTER = 8504553407  
    CURRENT_TOKEN = '8331141429:AAGeDiqh7Wqk0fiOQMDNbPSGTuXztIP0SzA'
    IS_SUB_BOT = False

# أسماء ملفات البيانات بناءً على آيدي المالك
ACCS_JSON = f'database_accounts_{CURRENT_MASTER}.json'
CONFIG_JSON = f'database_config_{CURRENT_MASTER}.json'

# --- [ نظام إدارة قاعدة البيانات المطور ] ---

def initialize_files():
    """تأكد من وجود الملفات الضرورية قبل بدء العمل"""
    for file in [ACCS_JSON, CONFIG_JSON]:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            logger.info(f"تم إنشاء ملف جديد: {file}")

def get_db(file_path):
    """قراءة البيانات من ملف JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"خطأ في قراءة الملف {file_path}: {e}")
        return {}

def set_db(file_path, data):
    """حفظ البيانات في ملف JSON بتنسيق مرتب"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"خطأ في حفظ الملف {file_path}: {e}")

# --- [ وظائف الفحص والتحقق ] ---

async def verify_session_and_phone(session_str, phone_input):
    """التحقق من صحة السيشن ومطابقة الرقم المدخل"""
    client = None
    try:
        # استخدام إعدادات جهاز ثابتة لتقليل الشك
        client = TelegramClient(
            StringSession(session_str), 
            API_ID, 
            API_HASH,
            device_model="Smart Factory Pro",
            system_version="Linux 5.15"
        )
        await client.connect()
        
        if not await client.is_user_authorized():
            return False, "السيشن منتهي أو غير صالح.", None

        me = await client.get_me()
        # تنظيف الأرقام للمقارنة
        clean_input = re.sub(r'\D', '', phone_input)
        clean_actual = re.sub(r'\D', '', me.phone)

        if clean_input not in clean_actual:
            return False, f"الرقم غير مطابق! السيشن يخص +{clean_actual}", None
            
        return True, "نجح التحقق", me
    except Exception as e:
        return False, str(e), None
    finally:
        if client:
            await client.disconnect()

# --- [ المهام الخلفية - تجميع الهدية ] ---

async def background_farm_worker():
    """مهمة تعمل في الخلفية لتجميع الهدية اليومية من جميع الحسابات"""
    while True:
        logger.info("بدء دورة التجميع التلقائي لجميع الحسابات...")
        db = get_db(ACCS_JSON)
        master_key = str(CURRENT_MASTER)
        
        if master_key in db:
            accounts = db[master_key].get('accounts', {})
            target = db[master_key].get('target_bot', '@t06bot')
            
            for phone, data in accounts.items():
                try:
                    client = TelegramClient(StringSession(data['ss']), API_ID, API_HASH)
                    await client.connect()
                    
                    if await client.is_user_authorized():
                        # إرسال ستارت للبوت المستهدف
                        await client.send_message(target, "/start")
                        await asyncio.sleep(3)
                        
                        # قراءة آخر رسالة للضغط على الأزرار
                        messages = await client.get_messages(target, limit=1)
                        if messages and messages[0].reply_markup:
                            for row in messages[0].reply_markup.rows:
                                for btn in row.buttons:
                                    if any(word in btn.text for word in ["هدية", "يومية", "تجميع"]):
                                        await messages[0].click(text=btn.text)
                                        logger.info(f"تم تجميع الهدية للرقم: {phone}")
                    
                    await client.disconnect()
                except Exception as e:
                    logger.warning(f"فشل التجميع للحساب {phone}: {e}")
                
                # فاصل زمني بين كل حساب لتجنب ضغط السيرفر
                await asyncio.sleep(15)
        
        # الانتظار لمدة 24 ساعة قبل الدورة القادمة
        await asyncio.sleep(86400)

# --- [ واجهة البوت الرئيسية ] ---

bot = TelegramClient(f'session_bot_{CURRENT_MASTER}', API_ID, API_HASH).start(bot_token=CURRENT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def main_menu(event):
    """عرض اللوحة الرئيسية للمالك"""
    if event.sender_id != CURRENT_MASTER:
        return
        
    db = get_db(ACCS_JSON)
    config = get_db(CONFIG_JSON)
    user_accounts = db.get(str(CURRENT_MASTER), {}).get('accounts', {})
    
    welcome_msg = (
        "✨ **مرحباً بك في نظام المصنع المتكامل** ✨\n\n"
        f"👤 المالك: `{CURRENT_MASTER}`\n"
        f"📱 الحسابات المربوطة: `{len(user_accounts)}` / `{config.get('limit', 500)}`\n"
        f"📅 اشتراكك ينتهي: `{config.get('expiry', '2027-01-01')}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "استخدم الأزرار أدناه لإدارة منظومتك بفاعلية."
    )
    
    buttons = [
        [Button.inline("➕ إضافة حساب (سيشن)", data="add_session"), Button.inline("📥 أداة الاستخراج", data="send_tool")],
        [Button.inline("📊 تقرير الحسابات", data="view_stats"), Button.inline("🔍 فحص الحسابات", data="check_accounts")],
        [Button.inline("🚀 بدء التجميع الآن", data="force_farm"), Button.inline("➖ حذف حساب", data="delete_account")],
        [Button.inline("⚙️ الإعدادات", data="settings")]
    ]
    
    if not IS_SUB_BOT:
        buttons.append([Button.inline("👑 تنصيب بوت لزبون", data="deploy_client")])
        
    await event.reply(welcome_msg, buttons=buttons, parse_mode='markdown')

# --- [ معالجة الطلبات بالسيشن ] ---

@bot.on(events.CallbackQuery(data="add_session"))
async def handle_add_session(event):
    uid = str(event.sender_id)
    async with bot.conversation(event.sender_id, timeout=300) as conv:
        try:
            # طلب السيشن
            await conv.send_message("🔹 **خطوة 1:** يرجى إرسال الـ String Session الآن:")
            res_ss = await conv.get_response()
            session_str = res_ss.text.strip()
            
            # طلب الرقم
            await conv.send_message("🔹 **خطوة 2:** أرسل رقم الهاتف المرتبط (بدون +):")
            res_ph = await conv.get_response()
            phone_num = res_ph.text.strip()
            
            # عملية التحقق
            status_msg = await conv.send_message("🔄 جاري التحقق من البيانات والارتباط...")
            success, message, user_info = await verify_session_and_phone(session_str, phone_num)
            
            if success:
                db = get_db(ACCS_JSON)
                if uid not in db:
                    db[uid] = {'accounts': {}, 'target_bot': '@t06bot'}
                
                # إضافة البيانات للقاعدة
                db[uid]['accounts'][phone_num] = {
                    'ss': session_str,
                    'name': user_info.first_name,
                    'date': str(datetime.datetime.now().date()),
                    'status': 'Active'
                }
                set_db(ACCS_JSON, db)
                
                final_text = (
                    "✅ **تم الربط بنجاح!**\n\n"
                    f"👤 الحساب: `{user_info.first_name}`\n"
                    f"📱 الرقم: `{phone_num}`\n"
                    "سيتم تضمينه في دورة التجميع القادمة."
                )
                await status_msg.edit(final_text)
            else:
                await status_msg.edit(f"❌ **فشل التحقق:**\n`{message}`")
                
        except asyncio.TimeoutError:
            await conv.send_message("⚠️ انتهت مهلة الجلسة، يرجى المحاولة مرة أخرى.")
        except Exception as e:
            await conv.send_message(f"⚠️ خطأ غير متوقع: {e}")

# --- [ إرسال أداة الاستخراج للمستخدم ] ---

@bot.on(events.CallbackQuery(data="send_tool"))
async def handle_send_tool(event):
    tool_code = f"""
import os, asyncio
try:
    from telethon.sync import TelegramClient
    from telethon.sessions import StringSession
except:
    os.system('pip install telethon')
    from telethon.sync import TelegramClient
    from telethon.sessions import StringSession

# المصنع الذكي - أداة الربط الآمن
API_ID = {API_ID}
API_HASH = '{API_HASH}'

async def main():
    print("-" * 30)
    print("مستخرج السيشن الآمن")
    print("-" * 30)
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        session = client.session.save()
        print("\\nإليك كود السيشن الخاص بك:\\n")
        print(session)
        print("\\nانسخ الكود وأرسله للبوت الرئيسي.")
        input("\\nاضغط Enter للخروج...")

if __name__ == "__main__":
    asyncio.run(main())
"""
    file_name = f"extractor_{event.sender_id}.py"
    with open(file_name, "w", encoding='utf-8') as f:
        f.write(tool_code)
    
    await event.respond(
        "🛠️ **أداة استخراج السيشن الآمنة**\n\n"
        "1. حمل الملف المرفق.\n"
        "2. شغله باستخدام بايثون على جهازك.\n"
        "3. سجل دخولك وانسخ الكود الناتج.\n"
        "4. ارجع للبوت واضغط 'إضافة حساب'.",
        file=file_name
    )
    os.remove(file_name)

# --- [ إحصائيات الحسابات ] ---

@bot.on(events.CallbackQuery(data="view_stats"))
async def handle_stats(event):
    db = get_db(ACCS_JSON)
    accounts = db.get(str(event.sender_id), {}).get('accounts', {})
    
    if not accounts:
        return await event.answer("⚠️ لا توجد حسابات مضافة حالياً.", alert=True)
        
    stats_text = "📊 **تقرير الحسابات المربوطة:**\n\n"
    for i, (phone, data) in enumerate(accounts.items(), 1):
        stats_text += f"{i}- `{phone}` | {data['name']} | 🟢\n"
    
    stats_text += f"\n✅ الإجمالي: `{len(accounts)}` حساب."
    await event.respond(stats_text)

# --- [ نظام حذف الحسابات ] ---

@bot.on(events.CallbackQuery(data="delete_account"))
async def handle_delete_acc(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("🗑️ أرسل رقم الهاتف الذي تريد حذفه من القائمة:")
        target_phone = (await conv.get_response()).text.strip()
        
        db = get_db(ACCS_JSON)
        uid = str(event.sender_id)
        
        if uid in db and target_phone in db[uid]['accounts']:
            del db[uid]['accounts'][target_phone]
            set_db(ACCS_JSON, db)
            await conv.send_message(f"✅ تم حذف الحساب `{target_phone}` من القاعدة.")
        else:
            await conv.send_message("❌ هذا الرقم غير موجود في سجلاتك.")

# --- [ تنصيب بوت لزبون جديد - للمالك فقط ] ---

@bot.on(events.CallbackQuery(data="deploy_client"))
async def handle_deploy(event):
    if IS_SUB_BOT:
        return await event.answer("⚠️ هذا الخيار متاح للمطور الأساسي فقط.", alert=True)
        
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("⚙️ **إعداد بوت جديد لزبون:**\nأرسل توكن البوت (Bot Token):")
        token = (await conv.get_response()).text.strip()
        
        await conv.send_message("👤 أرسل آيدي الزبون (Telegram ID):")
        client_id = (await conv.get_response()).text.strip()
        
        await conv.send_message("⏳ عدد أيام الاشتراك (أرقام فقط):")
        days = (await conv.get_response()).text.strip()
        
        # إنشاء ملف إعدادات للزبون
        expiry = (datetime.datetime.now() + datetime.timedelta(days=int(days))).strftime('%Y-%m-%d')
        config_data = {"expiry": expiry, "limit": 500}
        set_db(f"config_{client_id}.json", config_data)
        
        # تشغيل البوت كعملية مستقلة
        try:
            subprocess.Popen([sys.executable, sys.argv[0], token, client_id])
            await conv.send_message(f"✅ تم تشغيل بوت الزبون بنجاح!\n📅 ينتهي في: `{expiry}`")
        except Exception as e:
            await conv.send_message(f"❌ فشل التشغيل: {e}")

# --- [ نقطة انطلاق السورس ] ---

if __name__ == '__main__':
    # التأكد من جاهزية الملفات
    initialize_files()
    
    # تشغيل مهمة التجميع في الخلفية
    loop = asyncio.get_event_loop()
    loop.create_task(background_farm_worker())
    
    logger.info("تم تشغيل البوت بنجاح.. بانتظار الأوامر.")
    bot.run_until_disconnected()
