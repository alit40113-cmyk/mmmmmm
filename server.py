import os, asyncio, json, datetime, re, sys, subprocess, time
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError, 
    PhoneCodeInvalidError, 
    PasswordHashInvalidError, 
    PhoneNumberInvalidError,
    FloodWaitError
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import StartBotRequest

# --- [ الإعدادات الأساسية ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

# التحقق من نوع التشغيل (مالك أم زبون)
if len(sys.argv) > 2:
    CURRENT_TOKEN = sys.argv[1]
    CURRENT_MASTER = int(sys.argv[2])
    IS_SUB_BOT = True
else:
    CURRENT_MASTER = 8504553407  
    CURRENT_TOKEN = '8331141429:AAGeDiqh7Wqk0fiOQMDNbPSGTuXztIP0SzA'
    IS_SUB_BOT = False

ACCS_FILE = f'accs_{CURRENT_MASTER}.json'
CONFIG_FILE = f'config_{CURRENT_MASTER}.json'

# --- [ إدارة قاعدة البيانات ] ---
def load_db(file):
    try:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {file}: {e}")
    return {}

def save_db(file, data):
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving {file}: {e}")

# --- [ وظيفة تخطي الاشتراك الإجباري ] ---
async def join_required_channels(client, bot_username):
    try:
        msg = await client.get_messages(bot_username, limit=1)
        if msg[0].reply_markup:
            for row in msg[0].reply_markup.rows:
                for button in row.buttons:
                    if button.url:
                        channel_username = button.url.split('/')[-1]
                        try:
                            await client(JoinChannelRequest(channel_username))
                            await asyncio.sleep(1)
                        except:
                            pass
    except Exception:
        pass

# --- [ دالة التجميع اليومي والهدية ] ---
async def gift_worker():
    print("🚀 تم تشغيل ماكينة التجميع التلقائي...")
    while True:
        db = load_db(ACCS_FILE)
        uid_str = str(CURRENT_MASTER)
        if uid_str in db:
            accounts = db[uid_str].get('accounts', {})
            target = db[uid_str].get('target_bot', '@t06bot')
            
            for phone, info in accounts.items():
                try:
                    client = TelegramClient(StringSession(info['ss']), API_ID, API_HASH)
                    await client.connect()
                    if not await client.is_user_authorized():
                        print(f"❌ حساب محظور أو جلسة منتهية: {phone}")
                        continue
                        
                    await client.send_message(target, "/start")
                    await asyncio.sleep(5)
                    
                    # محاولة الضغط على أزرار التجميع
                    history = await client.get_messages(target, limit=1)
                    if history[0].reply_markup:
                        for row in history[0].reply_markup.rows:
                            for btn in row.buttons:
                                if any(x in btn.text for x in ["هدية", "يومية", "تجميع", "الرصيد"]):
                                    await history[0].click(text=btn.text)
                                    await asyncio.sleep(2)
                    
                    await client.disconnect()
                    print(f"✅ تم التجميع بنجاح للحساب: {phone}")
                except Exception as e:
                    print(f"⚠️ خطأ في الحساب {phone}: {e}")
                await asyncio.sleep(10) # انتظار بين حساب وحساب لتجنب الحظر
                
        await asyncio.sleep(24 * 3600) # كرر كل 24 ساعة

# --- [ البوت الرئيسي ] ---
bot = TelegramClient(f'main_session_{CURRENT_MASTER}', API_ID, API_HASH).start(bot_token=CURRENT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id != CURRENT_MASTER:
        return
        
    db = load_db(ACCS_FILE)
    config = load_db(CONFIG_FILE)
    acc_data = db.get(str(CURRENT_MASTER), {}).get('accounts', {})
    count = len(acc_data)
    
    msg = (
        "👑 **أهلاً بك في لوحة تحكم المصنع المطور**\n\n"
        f"📊 عدد حساباتك الحالية: `{count}`\n"
        f"⏳ تاريخ انتهاء الاشتراك: `{config.get('expiry', '2027-01-01')}`\n"
        f"📱 الحد الأقصى للأرقام: `{config.get('max_accounts', 500)}`\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    
    buttons = [
        [Button.inline("➕ إضافة رقم تلقائي", data="add_num"), Button.inline("➖ حذف رقم", data="del_num")],
        [Button.inline("📊 إحصائيات الحسابات", data="stats_all")],
        [Button.inline("🚀 تشغيل التجميع", data="run_farm"), Button.inline("🔍 فحص الحسابات", data="check_alive")],
        [Button.inline("💰 رصيد النقاط", data="balance"), Button.inline("💸 تحويل النقاط", data="transfer")],
    ]
    
    if not IS_SUB_BOT:
        buttons.append([Button.inline("💎 تنصيب بوت لزبون جديد", data="deploy_new")])
        
    await event.reply(msg, buttons=buttons)

# --- [ معالج الإضافة التلقائية (أهم جزء) ] ---
@bot.on(events.CallbackQuery(data="add_num"))
async def add_account_callback(event):
    uid_str = str(event.sender_id)
    db = load_db(ACCS_FILE)
    config = load_db(CONFIG_FILE)
    
    if len(db.get(uid_str, {}).get('accounts', {})) >= config.get('max_accounts', 500):
        return await event.answer("⚠️ عذراً، لقد تجاوزت الحد المسموح به من الأرقام!", alert=True)

    async with bot.conversation(event.sender_id) as conv:
        try:
            prompt1 = await conv.send_message("📞 **يرجى إرسال رقم الهاتف الآن:**\nمع رمز الدولة (مثال: `+9647800000000`)")
            phone = (await conv.get_response()).text.strip()
            
            temp_client = TelegramClient(StringSession(), API_ID, API_HASH)
            await temp_client.connect()
            
            await temp_client.send_code_request(phone)
            await conv.send_message("📩 **أرسل الكود المكون من 5 أرقام:**\n(وصلك في تطبيق التيليجرام)")
            code = (await conv.get_response()).text.strip().replace(" ", "")
            
            try:
                await temp_client.sign_in(phone, code)
            except SessionPasswordNeededError:
                await conv.send_message("🔐 **الحساب محمي بالتحقق بخطوتين.**\nأرسل كلمة السر الخاصة بك:")
                password = (await conv.get_response()).text
                await temp_client.sign_in(password=password)
            
            # حفظ البيانات
            new_session = temp_client.session.save()
            if uid_str not in db:
                db[uid_str] = {'accounts': {}, 'target_bot': '@t06bot'}
            
            db[uid_str]['accounts'][phone] = {
                'ss': new_session,
                'added_at': str(datetime.datetime.now()),
                'balance': 0
            }
            save_db(ACCS_FILE, db)
            
            await conv.send_message(f"✅ **تم ربط الحساب بنجاح!**\n📱 الرقم: `{phone}`\n🤖 سيتم التجميع منه تلقائياً.")
            await temp_client.disconnect()
            
        except Exception as e:
            await conv.send_message(f"❌ **فشل الربط!**\nالسبب: `{str(e)}`")

# --- [ معالجات الأزرار الأخرى ] ---
@bot.on(events.CallbackQuery(data="stats_all"))
async def stats_callback(event):
    db = load_db(ACCS_FILE)
    accounts = db.get(str(event.sender_id), {}).get('accounts', {})
    if not accounts:
        return await event.answer("⚠️ لا يوجد حسابات مضافة حالياً.", alert=True)
    
    report = "📊 **إحصائيات الحسابات:**\n\n"
    for i, (ph, info) in enumerate(accounts.items(), 1):
        report += f"{i}- `{ph}` | 📅 {info['added_at'][:10]}\n"
    
    await event.respond(report)

@bot.on(events.CallbackQuery(data="deploy_new"))
async def deploy_callback(event):
    if IS_SUB_BOT: return
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("⚙️ **أرسل توكن بوت الزبون:**")
        token = (await conv.get_response()).text
        await conv.send_message("👤 **أرسل آيدي الزبون:**")
        user_id = (await conv.get_response()).text
        await conv.send_message("⏳ **عدد أيام الاشتراك:**")
        days = (await conv.get_response()).text
        
        expiry_date = (datetime.datetime.now() + datetime.timedelta(days=int(days))).strftime('%Y-%m-%d')
        config_data = {"expiry": expiry_date, "max_accounts": 500}
        
        with open(f"config_{user_id}.json", "w") as f:
            json.dump(config_data, f)
            
        subprocess.Popen([sys.executable, sys.argv[0], token, user_id])
        await conv.send_message(f"✅ **تم تنصيب البوت بنجاح!**\n📅 ينتهي في: `{expiry_date}`")

# --- [ تشغيل البوت والمهام الجانبية ] ---
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(gift_worker())
    print("✅ البوت يعمل الآن بكفاءة عالية...")
    bot.run_until_disconnected()
