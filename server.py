import os, asyncio, json, datetime, re, sys, subprocess
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import StartBotRequest

# --- [ إعدادات الهوية الأساسية ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

# فحص: هل هذا بوت زبون أم البوت المصنع الأساسي؟
if len(sys.argv) > 2:
    CURRENT_TOKEN = sys.argv[1]
    CURRENT_MASTER = int(sys.argv[2])
    IS_SUB_BOT = True
else:
    CURRENT_MASTER = 8504553407  
    CURRENT_TOKEN = '8331141429:AAGeDiqh7Wqk0fiOQMDNbPSGTuXztIP0SzA'
    IS_SUB_BOT = False

# ملف بيانات مستقل لكل مالك بوت
ACCS_FILE = f'database_user_{CURRENT_MASTER}.json'

def load_db(file):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return {}

def save_db(file, data):
    with open(file, 'w') as f: json.dump(data, f)

# --- [ 1. وظيفة تفعيل الرابط وتخطي الاشتراك الإجباري ] ---
async def activate_and_join(ss, phone, bot_user, ref_id, owner_id):
    try:
        client = TelegramClient(StringSession(ss), API_ID, API_HASH)
        await client.connect()
        
        # تفعيل الرابط (النقاط تذهب لصاحب الرابط)
        await client(StartBotRequest(bot=bot_user, referrer_id=int(owner_id), start_param=ref_id))
        await asyncio.sleep(3)
        
        # تخطي الاشتراك (الانضمام للقنوات الإجبارية)
        msg = await client.get_messages(bot_user, limit=1)
        if msg[0].reply_markup:
            for row in msg[0].reply_markup.rows:
                for b in row.buttons:
                    if b.url:
                        # استخراج اسم القناة من الرابط والانضمام
                        channel_username = b.url.split('/')[-1]
                        try:
                            await client(JoinChannelRequest(channel_username))
                        except:
                            pass # في حال كانت القناة خاصة أو هناك خطأ
        
        # إرسال ستارت مرة ثانية للتأكد من التفعيل بعد الانضمام
        await client.send_message(bot_user, "/start")
        await client.disconnect()
    except Exception as e:
        print(f"Error in activation for {phone}: {e}")

# --- [ 2. ماكينة التجميع التلقائي للهدايا (خلفية) ] ---
async def daily_gift_worker():
    while True:
        db = load_db(ACCS_FILE)
        uid_str = str(CURRENT_MASTER)
        if uid_str in db:
            target_bot = db[uid_str].get('target_bot', '@t06bot')
            for phone, info in db[uid_str].get('accounts', {}).items():
                try:
                    client = TelegramClient(StringSession(info['ss']), API_ID, API_HASH)
                    await client.connect()
                    await client.send_message(target_bot, "/start")
                    await asyncio.sleep(4)
                    
                    # الخطوة الأولى: البحث عن زر "زيادة النقاط"
                    msg1 = await client.get_messages(target_bot, limit=1)
                    found_increase = False
                    if msg1[0].reply_markup:
                        for row in msg1[0].reply_markup.rows:
                            for btn in row.buttons:
                                if "زيادة" in btn.text or "تجميع" in btn.text:
                                    await msg1[0].click(text=btn.text)
                                    found_increase = True
                                    break
                    
                    if found_increase:
                        await asyncio.sleep(3)
                        # الخطوة الثانية: البحث عن زر "الهدية اليومية"
                        msg2 = await client.get_messages(target_bot, limit=1)
                        if msg2[0].reply_markup:
                            for row in msg2[0].reply_markup.rows:
                                for btn in row.buttons:
                                    if "هدية" in btn.text or "الهدية" in btn.text:
                                        await msg2[0].click(text=btn.text)
                                        # إضافة 1000 نقطة وهمية للمتابعة في البوت
                                        db[uid_str]['accounts'][phone]['balance'] = db[uid_str]['accounts'][phone].get('balance', 0) + 1000 
                    
                    await client.disconnect()
                except:
                    continue
            save_db(ACCS_FILE, db)
        
        # الانتظار 24 ساعة للدورة القادمة
        await asyncio.sleep(24 * 3600)

# --- [ 3. البوت الرئيسي والتحكم ] ---
bot = TelegramClient(f'session_bot_{CURRENT_MASTER}', API_ID, API_HASH).start(bot_token=CURRENT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id != CURRENT_MASTER:
        return await event.reply("❌ البوت خاص بمشترك معين.")
    
    markup = [
        [Button.inline("➕ إضافة حساب", data="add_acc"), Button.inline("➖ حذف حساب", data="del_acc")],
        [Button.inline("🚀 تفعيل الرابط (50 رقم)", data="start_farming")],
        [Button.inline("📊 فحص الرصيد", data="check_points")],
        [Button.inline("💰 تحويل 10,000 نقطة", data="transfer_now")],
    ]
    # زر المصنع يظهر للمالك الأساسي فقط وفي البوت الأساسي
    if not IS_SUB_BOT and event.sender_id == 8504553407:
        markup.append([Button.inline("💎 [مصنع] تنصيب لزبون", data="deploy_bot")])
    
    await event.reply("**💎 سورس العرب المتكامل (النسخة النهائية)**\n\n- نظام التجميع والتحويل وتخطي الاشتراك مفعل.", buttons=markup)

@bot.on(events.CallbackQuery(data="deploy_bot"))
async def deploy_logic(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("⚙️ أرسل توكن بوت الزبون:")
        token_input = (await conv.get_response()).text
        await conv.send_message("👤 أرسل آيدي (ID) الزبون:")
        id_input = (await conv.get_response()).text
        
        # تشغيل السورس كعملية جديدة لهذا الزبون
        subprocess.Popen([sys.executable, sys.argv[0], token_input, id_input])
        await conv.send_message("✅ تم تشغيل بوت الزبون بنجاح!")

@bot.on(events.CallbackQuery(data="add_acc"))
async def add_logic(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("🔹 أرسل كود الـ (String Session):")
        ss_val = (await conv.get_response()).text
        await conv.send_message("🔹 أرسل رقم الهاتف:")
        ph_val = (await conv.get_response()).text
        
        db = load_db(ACCS_FILE)
        uid = str(event.sender_id)
        if uid not in db: db[uid] = {'accounts': {}, 'target_bot': '@t06bot'}
        
        db[uid]['accounts'][ph_val] = {'ss': ss_val, 'balance': 0}
        save_db(ACCS_FILE, db)
        await conv.send_message(f"✅ تم إضافة الحساب {ph_val}")

@bot.on(events.CallbackQuery(data="check_points"))
async def check_logic(event):
    db = load_db(ACCS_FILE)
    accs = db.get(str(event.sender_id), {}).get('accounts', {})
    if not accs: return await event.answer("⚠️ لا توجد حسابات.", alert=True)
    
    msg = "📊 **إحصائيات حساباتك:**\n\n"
    for ph, info in accs.items():
        msg += f"📱 `{ph}` : {info.get('balance', 0)} نقطة\n"
    await event.respond(msg)

@bot.on(events.CallbackQuery(data="start_farming"))
async def farming_logic(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("🔗 أرسل رابط الدعوة المراد تفعيله:")
        link_text = (await conv.get_response()).text
        match = re.search(r"t\.me/([\w_]+)\?start=([\w\d]+)", link_text)
        if not match: return await conv.send_message("❌ الرابط غير صحيح.")
        
        bot_user, ref_id = match.group(1), match.group(2)
        db = load_db(ACCS_FILE)
        uid = str(event.sender_id)
        db[uid]['target_bot'] = f"@{bot_user}"
        save_db(ACCS_FILE, db)
        
        await conv.send_message("🚀 جاري بدء تفعيل الأرقام وتخطي الاشتراك...")
        for ph, info in db[uid]['accounts'].items():
            asyncio.create_task(activate_and_join(info['ss'], ph, bot_user, ref_id, event.sender_id))
        await conv.send_message("✅ اكتملت المهمة!")

@bot.on(events.CallbackQuery(data="transfer_now"))
async def transfer_logic(event):
    db = load_db(ACCS_FILE)
    uid = str(event.sender_id)
    limit = 10000
    target = db.get(uid, {}).get('target_bot', '@t06bot')
    
    await event.answer("⏳ جاري فحص وتحويل الحسابات (10k+)...", alert=False)
    for ph, info in db.get(uid, {}).get('accounts', {}).items():
        if info.get('balance', 0) >= limit:
            try:
                cl = TelegramClient(StringSession(info['ss']), API_ID, API_HASH)
                await cl.connect()
                # أمر التحويل لبوت المليار/الصقر
                await cl.send_message(target, f"نقل {event.sender_id} كل النقاط")
                db[uid]['accounts'][ph]['balance'] = 0
                await cl.disconnect()
            except: continue
    save_db(ACCS_FILE, db)
    await event.respond("✅ تم تحويل النقاط من جميع الحسابات المؤهلة.")

# --- [ الإقلاع النهائي ] ---
if __name__ == '__main__':
    print(f"🚀 البوت {'الفرعي' if IS_SUB_BOT else 'الأساسي'} انطلق...")
    loop = asyncio.get_event_loop()
    loop.create_task(daily_gift_worker())
    bot.run_until_disconnected()
