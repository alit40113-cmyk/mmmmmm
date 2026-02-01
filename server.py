import os, asyncio, json, datetime, re
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import StartBotRequest

# --- [ إعدادات المالك ] ---
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
                        # الضغط على زيادة النقاط
                        for row in msgs[0].reply_markup.rows:
                            for btn in row.buttons:
                                if "زيادة" in btn.text or "تجميع" in btn.text:
                                    await msgs[0].click(text=btn.text)
                                    await asyncio.sleep(2)
                                    break
                        
                        # الضغط على الهدية اليومية
                        new_msgs = await client.get_messages(target_bot, limit=1)
                        for row in new_msgs[0].reply_markup.rows:
                            for btn in row.buttons:
                                if "هدية" in btn.text or "الهدية" in btn.text:
                                    await new_msgs[0].click(text=btn.text)
                                    db[user_id]['accounts'][phone]['balance'] += 1000 
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

# --- [ 3. البوت الرئيسي ولوحة الأوامر ] ---
bot = TelegramClient('master_session', API_ID, API_HASH).start(bot_token=MASTER_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    is_master = event.sender_id == MASTER_ID
    btns = [
        [Button.inline("➕ اضافه حساب", data="add_acc"), Button.inline("➖ مسح حساب", data="del_acc")],
        [Button.inline("📲 الارقام الخاصه بك", data="my_nums")],
        [Button.inline("🚀 بدء التجميع (تفعيل الرابط)", data="start_farming")],
        [Button.inline("📊 فحص رصيد الحسابات", data="check_points")],
        [Button.inline("💰 تحويل النقاط المكتملة", data="transfer_now")],
        [Button.url("المطور", url="https://t.me/Alikhalafm")]
    ]
    if is_master:
        btns.append([Button.inline("💎 [المالك] تنصيب لزبون جديد", data="deploy")])
    
    await event.reply("**أهلاً بك في سورس العرب المتكامل**\n\n- نظام التجميع اليومي والتحويل الذكي (10k) مفعل.", buttons=btns)

@bot.on(events.CallbackQuery(data="start_farming"))
async def farming(event):
    uid = str(event.sender_id)
    db = load_db(ACCS_FILE)
    if uid not in db: return await event.answer("⚠️ لا توجد أرقام مضافة!", alert=True)

    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("🔗 **أرسل رابط الدعوة الخاص بك لتفعيل الأرقام منه:**")
        link = (await conv.get_response()).text
        match = re.search(r"t\.me/([\w_]+)\?start=([\w\d]+)", link)
        if not match: return await conv.send_message("❌ الرابط غير صحيح.")
        
        bot_user, ref_id = match.group(1), match.group(2)
        db[uid]['target_bot'] = f"@{bot_user}"
        save_db(ACCS_FILE, db)

        await conv.send_message(f"🚀 جاري تفعيل الحسابات من رابطك وتخطي الاشتراك...")
        for phone, info in db[uid]['accounts'].items():
            asyncio.create_task(activate_and_join(info['ss'], phone, bot_user, ref_id, event.sender_id))
            await asyncio.sleep(2)
        await conv.send_message("✅ اكتمل التفعيل. النقاط وصلت لحسابك، والأرقام بدأت تجمع الهدية يومياً.")

@bot.on(events.CallbackQuery(data="transfer_now"))
async def transfer(event):
    uid = str(event.sender_id)
    db = load_db(ACCS_FILE)
    limit = 10000 
    target_bot = db.get(uid, {}).get('target_bot', '@t06bot')
    
    await event.answer("⏳ جاري تحويل الحسابات الواصلة لـ 10,000 نقطة...", alert=False)
    for phone, info in db.get(uid, {}).get('accounts', {}).items():
        if info.get('balance', 0) >= limit:
            try:
                client = TelegramClient(StringSession(info['ss']), API_ID, API_HASH)
                await client.connect()
                await client.send_message(target_bot, f"نقل {event.sender_id} كل النقاط")
                db[uid]['accounts'][phone]['balance'] = 0 
                await client.disconnect()
            except: continue
    save_db(ACCS_FILE, db)
    await event.respond("✅ اكتملت عملية تحويل الحسابات المؤهلة.")

# --- [ إقلاع السورس ] ---
if __name__ == '__main__':
    print("🚀 السورس يعمل الآن بكامل طاقته...")
    loop = asyncio.get_event_loop()
    # تم تعديل الاسم هنا ليطابق الدالة في الأعلى
    loop.create_task(daily_gift_worker()) 
    bot.run_until_disconnected()
