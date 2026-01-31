import logging, base64, json, urllib.parse, os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8367617313:AAG8fb2THyKFw1qqHp5cyaxYXZOeiFdqLN4"
ADMIN_ID = 1049669606  # آيدي حسابك (رقم)
CHANNEL_USERNAME = "@teamofghost" # قناتك للاشتراك الإجباري
AUTHOR = "@Alikhalafm"
WHITELIST_FILE = "whitelist.json"

# تحميل قائمة الموافقة
if os.path.exists(WHITELIST_FILE):
    with open(WHITELIST_FILE, "r") as f: whitelist = json.load(f)
else: whitelist = []

BOT_ACTIVE = True
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# دالة فحص الاشتراك
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# أمر البدء ونظام طلب الانضمام
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not BOT_ACTIVE and user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ البوت متوقف حالياً.")
        return
    if not await is_subscribed(user.id, context):
        kb = [[InlineKeyboardButton("اضغط هنا للاشتراك 📢", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")]]
        await update.message.reply_text("❌ اشترك بالقناة أولاً ثم أرسل /start", reply_markup=InlineKeyboardMarkup(kb))
        return
    if user.id not in whitelist and user.id != ADMIN_ID:
        admin_kb = [[InlineKeyboardButton("✅ موافقة", callback_data=f"approve_{user.id}"), InlineKeyboardButton("❌ رفض", callback_data=f"decline_{user.id}")]]
        await context.bot.send_message(ADMIN_ID, f"🔔 طلب جديد:\nالاسم: {user.full_name}\nالآيدي: `{user.id}`", reply_markup=InlineKeyboardMarkup(admin_kb))
        await update.message.reply_text("⏳ تم إرسال طلبك للمالك، انتظر التفعيل.")
        return
    
    await update.message.reply_text(f"نورت حبي ، مبدأياً لازم ترسل /help\nوراح تستلم فيديوهين...\n\nرابط المختبر:\nhttps://www.skills.google/focuses/19155?parent=catalog\n\n{AUTHOR}")

# معالجة الرابط وصنع الملف (التفاعل المطلوب)
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in whitelist and user_id != ADMIN_ID: return
    text = update.message.text
    if "token=" not in text: return

    # رسائل التحميل التفاعلية
    status = await update.message.reply_text(f"✅ تم استلام الرابط. جاري التنفيذ الآن… {AUTHOR}")
    await asyncio.sleep(1)
    await status.edit_text(f"• ها ولك منيلك هذا البوت… {AUTHOR}")
    await asyncio.sleep(0.8)
    await status.edit_text(f"• 1) فتح رابط الطالب… {AUTHOR}\n• OK...")
    await asyncio.sleep(0.8)
    await status.edit_text(f"• ✅&\n• OK...\n• Cloud API ✅\n• Region ✅")
    await asyncio.sleep(0.8)
    await status.edit_text(f"• 3 ✅\n• 4 ✅\n• Create ✅")
    await asyncio.sleep(1)

    try:
        token = urllib.parse.parse_qs(urllib.parse.urlparse(text).query).get('token', [''])[0]
        domain = f"{AUTHOR.replace('@','')}-vip1-673647489483.us-central1.run.app"
        
        # بناء هيكل الملف المشفر بحقوقك 
        dark_structure = {
            "type": "VLESS",
            "name": f"VIP BY {AUTHOR}", # تغيير الحقوق هنا [cite: 1]
            "vlessTunnelConfig": {
                "v2rayConfig": {
                    "host": "alt13.yt3.ggpht.com", # 
                    "port": 443,
                    "uuid": token,
                    "serverNameIndication": "alt13.yt3.ggpht.com",
                    "wsPath": f"/Telegram/{AUTHOR}", # وضع معرفك في المسار 
                    "wsHeaderHost": domain
                },
                "injectConfig": {
                    "enabled": True, "mode": "PROXY", "proxyHost": "157.240.9.39",
                    "payload": f"CONNECT [host]:[port] HTTP/1.1[crlf]X-Developer: {AUTHOR}[crlf][crlf]" # الحقوق في البايلود 
                }
            }
        }
        
        encoded = base64.b64encode(json.dumps(dark_structure).encode()).decode()
        vless_link = f"vless://{token}@google.com:443?path=%2FTelegram%2F{AUTHOR}&security=tls&encryption=none&host={domain}&type=ws&sni={domain}#{AUTHOR}"
        
        final_msg = f"✅ عاشت ايدي،\n\nhttps://{domain}\n\n`{vless_link}`\n\n✅ DarkTunnel file جاهز للدومين:\n{domain}"
        await status.edit_text(final_msg)
        
        file_path = f"{AUTHOR}.dark"
        with open(file_path, "w") as f: f.write(f"darktunnel://{encoded}")
        with open(file_path, "rb") as f: await update.message.reply_document(f)
        os.remove(file_path)
    except: await status.edit_text("❌ خطأ في الرابط.")

# تفعيل الأزرار
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    target_id = int(data.split("_")[1])
    if data.startswith("approve_"):
        if target_id not in whitelist: whitelist.append(target_id)
        with open(WHITELIST_FILE, "w") as f: json.dump(whitelist, f)
        await query.edit_message_text(f"✅ تم تفعيل {target_id}")
        await context.bot.send_message(target_id, "🎉 تمت الموافقة! أرسل الرابط الآن.")
    else:
        await query.edit_message_text(f"❌ تم الرفض.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.run_polling()

if __name__ == "__main__": main()
