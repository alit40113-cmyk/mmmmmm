import os, asyncio, json, datetime, re, sys, subprocess
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import StartBotRequest

# --- [ إعدادات الهوية ] ---
# النظام هنا ذكي: إذا تم تشغيله من "المصنع" يأخذ بيانات الزبون، وإذا شغلته أنت يأخذ بياناتك.
if len(sys.argv) > 2:
    CURRENT_TOKEN = sys.argv[1]
    CURRENT_MASTER = int(sys.argv[2])
    IS_SUB_BOT = True
else:
    API_ID = 39719802 
    API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
    CURRENT_MASTER = 8504553407  
    CURRENT_TOKEN = '8331141429:AAGeDiqh7Wqk0fiOQMDNbPSGTuXztIP0SzA'
    IS_SUB_BOT = False

# ملفات منفصلة لكل مستخدم لضمان عدم تداخل البيانات
ACCS_FILE = f'accs_{CURRENT_MASTER}.json'

def load_db(file):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return {}

def save_db(file, data):
    with open(file, 'w') as f: json.dump(data, f)

# --- [ 1. وظيفة تفعيل الرابط وتخطي الاشتراك ] ---
async def activate_and_join(ss, phone, bot_user, ref_id, owner_id):
    try:
        client = TelegramClient(StringSession(ss), 39719802, '032a5697fcb9f3beeab8005d6601bde9')
        await client.connect()
        # تفعيل الرابط
        await client(StartBotRequest(bot=bot_user, referrer_id=int(owner_id), start_param=ref_id))
        await asyncio.sleep(2)
        # تخطي الاشتراك الإجباري
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

# --- [ 2. ماكينة التجميع اليومي الذكي ] ---
async def daily_gift_worker():
    while True:
        db = load_db(ACCS_FILE)
        uid_str = str(CURRENT_MASTER)
        if uid_str in db:
            target_bot = db[uid_str].get('target_bot', '@t06bot')
            for phone, info in db[uid_str].get('accounts', {}).items():
                try:
                    client = TelegramClient(StringSession(info['ss']), 39719802, '032a5697fcb9f3beeab8005d6601bde9')
                    await client.connect()
                    await client.send_message(target_bot, "/start")
                    await asyncio.sleep(3)
                    
                    # البحث عن "زيادة النقاط" ثم "الهدية"
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
                                    db[uid_str]['accounts'][phone]['balance'] = db[uid_str]['accounts'][phone].get('balance', 0) + 1000 
                    await client.disconnect()
                except: continue
            save_db(ACCS_FILE, db)
        await asyncio.sleep(24 * 3600)

# --- [ 3. البوت الرئيسي ولوحة التحكم ] ---
bot = TelegramClient(f'bot_session_{CURRENT_MASTER}', 39719802, '032a5697fcb9f3beeab8005d6601bde9').start(bot_token=CURRENT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id != CURRENT_MASTER:
        return await event.reply("❌ عذراً، هذا البوت مخصص لصاحبه فقط.")
    
    btns = [
        [Button.inline("➕ اضافه حساب", data="add_acc"), Button.inline("➖ مسح حساب", data="del_acc")],
        [Button.inline("🚀 بدء التجميع", data="start_farming")],
        [Button.inline("📊 فحص الرصيد", data="check_points")],
        [Button.inline("💰 تحويل النقاط المكتملة", data="transfer_now")],
    ]
    if not IS_SUB_BOT: # زر المصنع يظهر لك أنت فقط في بوتك الأساسي
        btns.append([Button.inline("💎 [المالك] تنصيب بوت لزبون", data="deploy_bot")])
    
    await event.reply("**أهلاً بك في النسخة النهائية من سورس العرب**\n\n- نظام المصنع والتجميع التلقائي مفعل.", buttons=btns)

@bot.on(events.CallbackQuery(data="deploy_bot"))
async def deploy(event):
    if IS_SUB_BOT: return
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("⚙️ **أرسل توكن بوت الزبون:**")
        tkn = (await conv.get_response()).text
        await conv.send_message("👤 **أرسل آيدي (ID) الزبون:**")
        uid = (await conv.get_response()).text
        # تشغيل البوت الجديد كعملية مستقلة
        subprocess.Popen([sys.executable, sys.argv[0], tkn, uid])
        await conv.send_message(f"✅ تم تشغيل بوت الزبون بنجاح!")

@bot.on(events.CallbackQuery(data="add_acc"))
async def add(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("🔹 أرسل كود الـ (String Session):")
        ss = (await conv.get_response()).text
        await conv.send_message("🔹 أرسل رقم الهاتف:")
        ph = (await conv.get_response()).text
        db = load_db(ACCS_FILE)
        uid = str(event.sender_id)
        if uid not in db: db[uid] = {'accounts': {}, 'target_bot': '@t06bot'}
        db[uid]['accounts'][ph] = {'ss': ss, 'balance': 0}
        save_db(ACCS_FILE, db)
        await conv.send_message(f"✅ تم إضافة {ph}")

@bot.on(events.CallbackQuery(data="check_points"))
async def check(event):
    db = load_db(ACCS_FILE)
    accs = db.get(str(event.sender_id), {}).get('accounts', {})
    if not accs: return await event.answer("⚠️ لا توجد أرقام.", alert=True)
    msg = "📊 **رصيد حساباتك:**\n\n"
    for ph, info in accs.items(): msg += f"📱 `{ph}` : {info.get('balance', 0)} نقطة\n"
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
        await conv.send_message("🚀 جاري تفعيل الـ 50 رقم...")
        for ph, info in db[uid]['accounts'].items():
            asyncio.create_task(activate_and_join(info['ss'], ph, bot_u, r_id, event.sender_id))
        await conv.send_message("✅ اكتمل التفعيل!")

@bot.on(events.CallbackQuery(data="transfer_now"))
async def transfer(event):
    db = load_db(ACCS_FILE)
    uid = str(event.sender_id)
    limit, t_bot = 10000, db.get(uid, {}).get('target_bot', '@t06bot')
    await event.answer("⏳ جاري التحويل...", alert=False)
    for ph, info in db.get(uid, {}).get('accounts', {}).items():
        if info.get('balance', 0) >= limit:
            try:
                cl = TelegramClient(StringSession(info['ss']), 39719802, '032a5697fcb9f3beeab8005d6601bde9')
                await cl.connect()
                await cl.send_message(t_bot, f"نقل {event.sender_id} كل النقاط")
                db[uid]['accounts'][ph]['balance'] = 0
                await cl.disconnect()
            except: continue
    save_db(ACCS_FILE, db)
    await event.respond("✅ تم تحويل كل الحسابات التي وصلت 10k.")

if __name__ == '__main__':
    print("🚀 السورس يعمل بكامل طاقته...")
    loop = asyncio.get_event_loop()
    loop.create_task(daily_gift_worker())
    bot.run_until_disconnected()
