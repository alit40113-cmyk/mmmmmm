import os, asyncio, json, datetime, re, sys, subprocess
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import StartBotRequest

# --- [ إعدادات التشغيل الذكي ] ---
# إذا تم تشغيل السورس من المصنع ببيانات زبون
if len(sys.argv) > 2:
    CURRENT_TOKEN = sys.argv[1]
    CURRENT_MASTER = int(sys.argv[2])
    IS_SUB_BOT = True
else:
    # إعداداتك أنت (المالك والمصنع الأساسي)
    API_ID = '39719802' 
    API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
    CURRENT_MASTER = 8504553407  
    CURRENT_TOKEN = '8331141429:AAGeDiqh7Wqk0fiOQMDNbPSGTuXztIP0SzA'
    IS_SUB_BOT = False

# ملفات البيانات (كل بوت زبون له ملف خاص حتى ما تتداخل الأرقام)
ACCS_FILE = f'accs_{CURRENT_MASTER}.json'
DB_FILE = 'factory_database.json'

def load_db(file):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return {}

def save_db(file, data):
    with open(file, 'w') as f: json.dump(data, f)

# --- [ 1. ماكينة التجميع اليومي ] ---
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

# --- [ 2. البوت ومعالجة الأوامر ] ---
bot = TelegramClient(f'session_{CURRENT_MASTER}', 39719802, '032a5697fcb9f3beeab8005d6601bde9').start(bot_token=CURRENT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    is_master = event.sender_id == CURRENT_MASTER
    # المالك الأساسي (أنت) فقط يرى زر التنصيب لزبون
    btns = [
        [Button.inline("➕ اضافه حساب", data="add_acc"), Button.inline("➖ مسح حساب", data="del_acc")],
        [Button.inline("🚀 بدء التجميع", data="start_farming")],
        [Button.inline("📊 فحص الرصيد", data="check_points")],
        [Button.inline("💰 تحويل النقاط", data="transfer_now")],
    ]
    # إذا كنت أنت المشغل للبوت وبوتك هو "المصنع"
    if is_master and not IS_SUB_BOT:
        btns.append([Button.inline("💎 [المالك] تنصيب بوت لزبون", data="deploy_bot")])
    
    await event.reply(f"🚀 **أهلاً بك في سورس العرب المتكامل**\n\n- البوت شغال وتحت سيطرتك.", buttons=btns)

# --- [ 3. منطق المصنع (خاص بك أنت فقط) ] ---
@bot.on(events.CallbackQuery(data="deploy_bot"))
async def deploy_bot(event):
    if IS_SUB_BOT or event.sender_id != 8504553407: return 
    
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("⚙️ **أرسل توكن بوت الزبون الجديد:**")
        tkn = (await conv.get_response()).text
        await conv.send_message("👤 **أرسل آيدي (ID) الزبون ليصبح مالكاً لبوطه:**")
        uid = (await conv.get_response()).text
        
        # تشغيل نسخة جديدة من نفس الملف بأوامر مختلفة
        subprocess.Popen([sys.executable, 'server.py', tkn, uid])
        await conv.send_message(f"✅ تم تشغيل بوت الزبون بنجاح!\nالآن يمكن للزبون الدخول لبوطه والبدء بالعمل.")

# --- [ 4. بقية المهام (إضافة، تجميع، تحويل) ] ---
@bot.on(events.CallbackQuery(data="add_acc"))
async def add(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message("🔹 أرسل كود الـ (String Session):")
        ss = (await conv.get_response()).text
        await conv.send_message("🔹 أرسل رقم الهاتف:")
        ph = (await conv.get_response()).text
        db = load_db(ACCS_FILE)
        uid = str(event.sender_id)
        if uid not in db: db[uid] = {'accounts': {}}
        db[uid]['accounts'][ph] = {'ss': ss, 'balance': 0}
        save_db(ACCS_FILE, db)
        await conv.send_message("✅ تمت الإضافة.")

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
            # دالة التفعيل كما في الأكواد السابقة...
            pass 
        await conv.send_message("🚀 جاري التفعيل...")

# --- [ إقلاع السورس ] ---
if __name__ == '__main__':
    print(f"🚀 البوت {'الفرعي' if IS_SUB_BOT else 'الأساسي'} يعمل الآن...")
    loop = asyncio.get_event_loop()
    loop.create_task(daily_gift_worker())
    bot.run_until_disconnected()
