import os, asyncio, json, datetime, re, sys, subprocess
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import StartBotRequest

# --- [ إعدادات الهوية والديناميكية ] ---
API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

if len(sys.argv) > 2:
    # إعدادات بوت الزبون (يتم استلامها من المصنع)
    CURRENT_TOKEN = sys.argv[1]
    CURRENT_MASTER = int(sys.argv[2])
    IS_SUB_BOT = True
else:
    # إعدادات المالك الأساسي (أنت)
    CURRENT_MASTER = 8504553407  
    CURRENT_TOKEN = '8331141429:AAGeDiqh7Wqk0fiOQMDNbPSGTuXztIP0SzA'
    IS_SUB_BOT = False

# ملفات البيانات والاشتراكات
ACCS_FILE = f'accs_{CURRENT_MASTER}.json'
CONFIG_FILE = f'config_{CURRENT_MASTER}.json'

def load_db(file):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return {}

def save_db(file, data):
    with open(file, 'w') as f: json.dump(data, f)

# --- [ 1. وظيفة تخطي الاشتراك والتفعيل ] ---
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

# --- [ 2. ماكينة التجميع اليومي ] ---
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

# --- [ 3. البوت الرئيسي ] ---
bot = TelegramClient(f'bot_{CURRENT_MASTER}', API_ID, API_HASH).start(bot_token=CURRENT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id != CURRENT_MASTER: return
    
    config = load_db(CONFIG_FILE)
    expiry = config.get('expiry', 'غير محدود')
    limit = config.get('max_accounts', 'لا يوجد حد')

    btns = [
        [Button.inline("➕ إضافة حساب", data="add_acc"), Button.inline("➖ حذف حساب", data="del_acc")],
        [Button.inline("🚀 بدء التجميع", data="start_farming")],
        [Button.inline("📊 فحص الرصيد", data="check_points")],
        [Button.inline("💰 تحويل 10,000", data="transfer_now")],
    ]
    if not IS_SUB_BOT: # المصنع يظهر لك أنت فقط
        btns.append([Button.inline("💎 [المالك] تنصيب لزبون", data="deploy_bot")])
    
    await event.reply(f"🚀 **سورس المصنع المطور**\n\n📅 انتهاء الاشتراك: `{expiry}`\n📱 حد الأرقام: `{limit}`", buttons=btns)

@bot.on(events.CallbackQuery(data="deploy_bot"))
async def deploy(event):
    if IS_SUB_BOT: return
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("⚙️ **أرسل توكن بوت الزبون:**")
        tkn = (await conv.get_response()).text
        await conv.send_message("👤 **أرسل آيدي (ID) الزبون:**")
        uid = (await conv.get_response()).text
        await conv.send_message("⏳ **عدد أيام الاشتراك (مثلاً: 30):**")
        days = (await conv.get_response()).text
        await conv.send_message("📱 **الحد الأقصى للأرقام (مثلاً: 50):**")
        mx = (await conv.get_response()).text

        # حفظ إعدادات الزبون قبل التشغيل
        exp = (datetime.datetime.now() + datetime.timedelta(days=int(days))).strftime('%Y-%m-%d')
        with open(f"config_{uid}.json", "w") as f:
            json.dump({"expiry": exp, "max_accounts": int(mx)}, f)
        
        # تشغيل البوت كعملية مستقلة
        subprocess.Popen([sys.executable, sys.argv[0], tkn, uid])
        await conv.send_message(f"✅ تم تشغيل بوت الزبون بنجاح!")

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
        await conv.send_message("🔹 أرسل الرقم:")
        ph = (await conv.get_response()).text
        if uid_str not in db: db[uid_str] = {'accounts': {}, 'target_bot': '@t06bot'}
        db[uid_str]['accounts'][ph] = {'ss': ss, 'balance': 0}
        save_db(ACCS_FILE, db)
        await conv.send_message("✅ تم الحفظ.")

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
        await conv.send_message("🚀 جاري التفعيل...")

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
