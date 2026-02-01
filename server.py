import os, asyncio, json, datetime, re
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import StartBotRequest

# --- [ إعدادات المالك الأساسية ] ---
API_ID = '39719802' 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
MASTER_ID = 8504553407  
MASTER_TOKEN = '8331141429:AAGeDiqh7Wqk0fiOQMDNbPSGTuXztIP0SzA'

ACCS_FILE = 'accounts_data.json'
DB_FILE = 'master_db.json'

def load_db(file):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return {}

def save_db(file, data):
    with open(file, 'w') as f: json.dump(data, f)

# --- [ 1. ماكينة التجميع اليومي الذكي ] ---
async def daily_gift_worker():
    while True:
        db = load_db(ACCS_FILE)
        for user_id, user_data in db.items():
            target_bot = user_data.get('target_bot', '@t06bot')
            for phone, info in user_data.get('accounts', {}).items():
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
                                    db[user_id]['accounts'][phone]['balance'] = db[user_id]['accounts'][phone].get('balance', 0) + 1000 
                    await client.disconnect()
                except: continue
        save_db(ACCS_FILE, db)
        await asyncio.sleep(24 * 3600)

# --- [ 2. وظيفة تفعيل الرابط وتخطي الاشتراك ] ---
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

# --- [ 3. البوت الرئيسي ومعالجة الأوامر ] ---
bot = TelegramClient('master_session', API_ID, API_HASH).start(bot_token=MASTER_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = str(event.sender_id)
    m_db = load_db(DB_FILE)
    is_master = event.sender_id == MASTER_ID
    is_client = uid in m_db and datetime.datetime.strptime(m_db[uid]['expiry'], '%Y-%m-%d') > datetime.datetime.now()

    if not is_master and not is_client:
        return await event.reply("❌ **اشتراكك غير مفعل.**\nللتواصل مع المطور: @Alikhalafm")

    btns = [
        [Button.inline("➕ اضافه حساب", data="add_acc"), Button.inline("➖ مسح حساب", data="del_acc")],
        [Button.inline("🚀 بدء التجميع (تفعيل الرابط)", data="start_farming")],
        [Button.inline("📊 فحص رصيد الحسابات", data="check_points")],
        [Button.inline("💰 تحويل النقاط المكتملة", data="transfer_now")],
        [Button.url("المطور", url="https://t.me/Alikhalafm")]
    ]
    if is_master: btns.append([Button.inline("💎 [المالك] تنصيب لزبون", data="deploy")])
    await event.reply(f"✅ **أهلاً بك.. السورس يعمل بنجاح!**\n📅 انتهاء الاشتراك: {m_db.get(uid, {}).get('expiry', 'غير محدود')}", buttons=btns)

@bot.on(events.CallbackQuery(data="deploy"))
async def deploy(event):
    if event.sender_id != MASTER_ID: return
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("👤 أرسل آيدي (ID) الزبون:")
        u_id = (await conv.get_response()).text
        await conv.send_message("⏳ كم يوماً؟")
        days = (await conv.get_response()).text
        await conv.send_message("📱 أقصى عدد حسابات؟")
        mx = (await conv.get_response()).text
        m_db = load_db(DB_FILE)
        m_db[u_id] = {'expiry': (datetime.datetime.now() + datetime.timedelta(days=int(days))).strftime('%Y-%m-%d'), 'max': int(mx)}
        save_db(DB_FILE, m_db)
        await conv.send_message("✅ تم التفعيل بنجاح.")

@bot.on(events.CallbackQuery(data="add_acc"))
async def add(event):
    uid = str(event.sender_id)
    m_db = load_db(DB_FILE)
    db = load_db(ACCS_FILE)
    current_count = len(db.get(uid, {}).get('accounts', {}))
    max_allowed = m_db.get(uid, {}).get('max', 1000)
    
    if not (event.sender_id == MASTER_ID) and current_count >= max_allowed:
        return await event.answer(f"⚠️ وصلت للحد الأقصى ({max_allowed} رقم)!", alert=True)

    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("🔹 أرسل كود الـ (String Session):")
        ss = (await conv.get_response()).text
        await conv.send_message("🔹 أرسل رقم الهاتف:")
        ph = (await conv.get_response()).text
        if uid not in db: db[uid] = {'accounts': {}, 'target_bot': '@t06bot'}
        db[uid]['accounts'][ph] = {'ss': ss, 'balance': 0}
        save_db(ACCS_FILE, db)
        await conv.send_message("✅ تم الإضافة.")

@bot.on(events.CallbackQuery(data="check_points"))
async def check(event):
    db = load_db(ACCS_FILE)
    accs = db.get(str(event.sender_id), {}).get('accounts', {})
    if not accs: return await event.answer("⚠️ لا توجد حسابات.", alert=True)
    msg = "📊 **الرصيد:**\n"
    for ph, info in accs.items(): msg += f"📱 `{ph}`: {info.get('balance',0)}\n"
    await event.respond(msg)

@bot.on(events.CallbackQuery(data="start_farming"))
async def farming(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("🔗 أرسل رابط الدعوة:")
        link = (await conv.get_response()).text
        match = re.search(r"t\.me/([\w_]+)\?start=([\w\d]+)", link)
        if not match: return await conv.send_message("❌ رابط خطأ.")
        bot_u, r_id = match.group(1), match.group(2)
        db = load_db(ACCS_FILE)
        uid = str(event.sender_id)
        db[uid]['target_bot'] = f"@{bot_u}"
        save_db(ACCS_FILE, db)
        for ph, info in db[uid]['accounts'].items():
            asyncio.create_task(activate_and_join(info['ss'], ph, bot_u, r_id, event.sender_id))
        await conv.send_message("🚀 جاري التفعيل...")

@bot.on(events.CallbackQuery(data="transfer_now"))
async def transfer(event):
    db = load_db(ACCS_FILE)
    uid = str(event.sender_id)
    limit, t_bot = 10000, db.get(uid, {}).get('target_bot', '@t06bot')
    for ph, info in db.get(uid, {}).get('accounts', {}).items():
        if info.get('balance', 0) >= limit:
            try:
                cl = TelegramClient(StringSession(info['ss']), API_ID, API_HASH)
                await cl.connect()
                await cl.send_message(t_bot, f"نقل {event.sender_id} كل النقاط")
                db[uid]['accounts'][ph]['balance'] = 0
                await cl.disconnect()
            except: continue
    save_db(ACCS_FILE, db)
    await event.respond("✅ تم تحويل الجاهز.")

if __name__ == '__main__':
    print("🚀 السورس يعمل...")
    loop = asyncio.get_event_loop()
    loop.create_task(daily_gift_worker())
    bot.run_until_disconnected()
