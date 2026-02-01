import os, asyncio, json, datetime, re, sys, subprocess
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import StartBotRequest

# --- [ إعدادات الهوية ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

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

def load_db(file):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return {}

def save_db(file, data):
    with open(file, 'w') as f: json.dump(data, f)

# --- [ 1. وظيفة التحقق من السيشن والرقم ] ---
async def verify_account(ss, phone_input):
    try:
        clean_phone = re.sub(r'\D', '', phone_input)
        temp_client = TelegramClient(StringSession(ss), API_ID, API_HASH)
        await temp_client.connect()
        
        if not await temp_client.is_user_authorized():
            await temp_client.disconnect()
            return False, "⚠️ السيشن منتهي أو غير صالح!"
        
        me = await temp_client.get_me()
        actual_phone = re.sub(r'\D', '', me.phone)
        await temp_client.disconnect()
        
        if clean_phone not in actual_phone:
            return False, f"⚠️ الرقم غير مطابق! السيشن يخص: +{actual_phone}"
        
        return True, "✅ تم التحقق بنجاح"
    except Exception as e:
        return False, f"⚠️ خطأ في الفحص: {str(e)}"

# --- [ 2. وظيفة تخطي الاشتراك والتفعيل ] ---
async def activate_and_join(ss, phone, bot_user, ref_id, owner_id):
    try:
        client = TelegramClient(StringSession(ss), API_ID, API_HASH)
        await client.connect()
        await client(StartBotRequest(bot=bot_user, referrer_id=int(owner_id), start_param=ref_id))
        await asyncio.sleep(2)
        msg = await client.get_messages(bot_user, limit=1)
        if msg[0].reply_markup:
            for row in msg[0].reply_markup.rows:
                for b in row.buttons:
                    if b.url:
                        try: await client(JoinChannelRequest(b.url.split('/')[-1]))
                        except: pass
        await client.send_message(bot_user, "/start")
        await client.disconnect()
    except: pass

# --- [ 3. ماكينة التجميع اليومي ] ---
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
                    await asyncio.sleep(3)
                    msgs = await client.get_messages(target_bot, limit=1)
                    if msgs[0].reply_markup:
                        for row in msgs[0].reply_markup.rows:
                            for btn in row.buttons:
                                if any(x in btn.text for x in ["زيادة", "تجميع"]):
                                    await msgs[0].click(text=btn.text)
                                    await asyncio.sleep(2)
                                    break
                        new_msgs = await client.get_messages(target_bot, limit=1)
                        for row in new_msgs[0].reply_markup.rows:
                            for btn in row.buttons:
                                if any(x in btn.text for x in ["هدية", "الهدية"]):
                                    await new_msgs[0].click(text=btn.text)
                                    db[uid_str]['accounts'][phone]['balance'] += 1000 
                    await client.disconnect()
                except: continue
            save_db(ACCS_FILE, db)
        await asyncio.sleep(24 * 3600)

# --- [ 4. البوت الرئيسي ] ---
bot = TelegramClient(f'bot_{CURRENT_MASTER}', API_ID, API_HASH).start(bot_token=CURRENT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id != CURRENT_MASTER: return
    
    config = load_db(CONFIG_FILE)
    db = load_db(ACCS_FILE)
    accs_count = len(db.get(str(CURRENT_MASTER), {}).get('accounts', {}))
    
    btns = [
        [Button.inline("➕ إضافة حساب", data="add_acc"), Button.inline("➖ حذف حساب", data="del_acc")],
        [Button.inline(f"📊 حساباتك: {accs_count}", data="stats")],
        [Button.inline("🚀 بدء التجميع", data="start_farming")],
        [Button.inline("📊 فحص الرصيد", data="check_points")],
        [Button.inline("💰 تحويل 10,000", data="transfer_now")],
    ]
    if not IS_SUB_BOT:
        btns.append([Button.inline("💎 [المالك] تنصيب لزبون", data="deploy_bot")])
    
    await event.reply(f"🚀 **سورس المصنع المطور**\n📅 انتهاء الاشتراك: `{config.get('expiry', 'غير محدود')}`", buttons=btns)

@bot.on(events.CallbackQuery(data="stats"))
async def stats_handler(event):
    db = load_db(ACCS_FILE)
    accs = db.get(str(event.sender_id), {}).get('accounts', {})
    await event.answer(f"📱 مجموع حساباتك المضافة: {len(accs)}", alert=True)

@bot.on(events.CallbackQuery(data="add_acc"))
async def add(event):
    config = load_db(CONFIG_FILE)
    db = load_db(ACCS_FILE)
    uid_str = str(event.sender_id)
    current_count = len(db.get(uid_str, {}).get('accounts', {}))
    max_limit = config.get('max_accounts', 1000)

    if current_count >= max_limit:
        return await event.answer(f"⚠️ وصلت للحد الأقصى ({max_limit} رقم)!", alert=True)

    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("🔹 أرسل كود الـ (String Session):")
        ss = (await conv.get_response()).text
        await conv.send_message("🔹 أرسل رقم الهاتف المرتبط:")
        ph = (await conv.get_response()).text
        
        load_msg = await conv.send_message("🔍 جاري التحقق من صحة البيانات...")
        is_ok, result = await verify_account(ss, ph)
        
        if is_ok:
            if uid_str not in db: db[uid_str] = {'accounts': {}, 'target_bot': '@t06bot'}
            db[uid_str]['accounts'][ph] = {'ss': ss, 'balance': 0}
            save_db(ACCS_FILE, db)
            await load_msg.edit(f"✅ {result}\nتم حفظ الحساب.")
        else:
            await load_msg.edit(f"❌ {result}")

@bot.on(events.CallbackQuery(data="deploy_bot"))
async def deploy(event):
    if IS_SUB_BOT: return
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("⚙️ **توكن الزبون:**")
        tkn = (await conv.get_response()).text
        await conv.send_message("👤 **آيدي الزبون:**")
        uid = (await conv.get_response()).text
        await conv.send_message("⏳ **الأيام:**")
        days = (await conv.get_response()).text
        await conv.send_message("📱 **حد الأرقام:**")
        mx = (await conv.get_response()).text

        exp = (datetime.datetime.now() + datetime.timedelta(days=int(days))).strftime('%Y-%m-%d')
        with open(f"config_{uid}.json", "w") as f:
            json.dump({"expiry": exp, "max_accounts": int(mx)}, f)
        
        subprocess.Popen([sys.executable, sys.argv[0], tkn, uid])
        await conv.send_message(f"✅ تم تشغيل بوت الزبون بنجاح!")

@bot.on(events.CallbackQuery(data="check_points"))
async def check(event):
    db = load_db(ACCS_FILE)
    accs = db.get(str(event.sender_id), {}).get('accounts', {})
    msg = "📊 **الرصيد:**\n"
    for ph, info in accs.items(): msg += f"📱 `{ph}`: {info.get('balance',0)}\n"
    await event.respond(msg if accs else "⚠️ لا توجد حسابات.")

@bot.on(events.CallbackQuery(data="start_farming"))
async def farming(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("🔗 أرسل رابط الدعوة:")
        link = (await conv.get_response()).text
        match = re.search(r"t\.me/([\w_]+)\?start=([\w\d]+)", link)
        if not match: return await conv.send_message("❌ رابط خطأ.")
        bot_u, r_id = match.group(1), match.group(2)
        db = load_db(ACCS_FILE)
        uid_str = str(event.sender_id)
        db[uid_str]['target_bot'] = f"@{bot_u}"
        save_db(ACCS_FILE, db)
        for ph, info in db[uid_str]['accounts'].items():
            asyncio.create_task(activate_and_join(info['ss'], ph, bot_u, r_id, event.sender_id))
        await conv.send_message("🚀 جاري التفعيل لجميع الحسابات...")

@bot.on(events.CallbackQuery(data="transfer_now"))
async def transfer(event):
    db = load_db(ACCS_FILE)
    uid_str = str(event.sender_id)
    limit, t_bot = 10000, db.get(uid_str, {}).get('target_bot', '@t06bot')
    for ph, info in db.get(uid_str, {}).get('accounts', {}).items():
        if info.get('balance', 0) >= limit:
            try:
                cl = TelegramClient(StringSession(info['ss']), API_ID, API_HASH)
                await cl.connect()
                await cl.send_message(t_bot, f"نقل {event.sender_id} كل النقاط")
                db[uid_str]['accounts'][ph]['balance'] = 0
                await cl.disconnect()
            except: continue
    save_db(ACCS_FILE, db)
    await event.respond("✅ تم التحويل.")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(daily_gift_worker())
    bot.run_until_disconnected()
